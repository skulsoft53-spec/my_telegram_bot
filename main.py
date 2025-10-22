import os
import threading
import asyncio
import random
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes
)

# -----------------------
# 🔑  Конфигурация
# -----------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Ошибка: TELEGRAM_TOKEN не установлен!")

OWNER_ID = 8486672898          # <-- твой Telegram ID
LOG_CHANNEL_ID = -1003107269526
bot_active = True

# Хранилище
last_messages = {}
saved_troll_template = None
troll_stop = False

# -----------------------
# Тексты
# -----------------------
LOVE_PHRASES = [
    "Ты мне дорог 💞", "Я рад, что ты есть 💫", "Ты особенная 💖", "Ты мой человек 💕",
    "С тобой спокойно 🌷", "Ты просто счастье 🌙", "Ты делаешь день лучше ☀️", "Ты важна 💝",
    "Ты мой уют 💗", "Ты как свет ✨", "Ты делаешь меня лучше 💐", "Ты моя радость 🌸",
    "Ты моё вдохновение 💓", "Ты просто прекрасна 💞", "Ты моё всё 💘"
]
LOVE_JOKES = ["Ты как Wi-Fi — рядом, и всё идеально 😄"]
LOVE_LEVELS = [
    (0, 10, "💔 Лёд между сердцами... но шанс есть."),
    (11, 25, "🌧️ Едва заметная искра."),
    (26, 45, "💫 Симпатия растёт."),
    (46, 65, "💞 Нежное притяжение."),
    (66, 80, "💖 Сердца бьются в унисон."),
    (81, 95, "💘 Это почти любовь."),
    (96, 100, "💍 Любовь навсегда."),
]
GIFTS_ROMANTIC = ["💐 Букет слов и немного нежности", "🍫 Шоколад из чувства симпатии"]
GIFTS_FUNNY = ["🍕 Один кусочек любви и три крошки заботы", "🍟 Картошка с соусом симпатии"]

# -----------------------
# Мини-вебсервер (для Render)
# -----------------------
def run_web():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"LoveBot is running <3")
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()

# -----------------------
# Вспомогательные функции
# -----------------------
async def send_log(context: ContextTypes.DEFAULT_TYPE, text: str):
    try:
        if context and context.bot:
            await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=text)
    except Exception:
        print("LOG:", text)

def split_smart_into_lines(text: str):
    """Разделяем текст шаблона на строки (если нет переносов — каждые 30-40 слов)."""
    if "\n" in text:
        return [ln.strip() for ln in text.split("\n") if ln.strip()]
    words = text.split()
    lines, i = [], 0
    step = random.randint(30, 40)
    while i < len(words):
        lines.append(" ".join(words[i:i+step]))
        i += step
    return lines

# -----------------------
# Команды управления
# -----------------------
async def onbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("🚫 Только владелец.")
    bot_active = True
    await update.message.reply_text("🔔 Бот снова активен!")

async def offbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if update.effective_user.id != OWNER_ID:
        return await update.message.reply_text("🚫 Только владелец.")
    bot_active = False
    await update.message.reply_text("⚠️ Бот отключён — отвечает только на команды.")

# -----------------------
# /trollsave — сохраняем шаблон
# -----------------------
async def trollsave_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global saved_troll_template
    if update.effective_user.id != OWNER_ID:
        return
    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2:
        return await update.message.reply_text("❌ Используй: /trollsave <текст>")
    text = parts[1].strip()
    saved_troll_template = split_smart_into_lines(text)
    await update.message.reply_text(f"✅ Шаблон сохранён: {len(saved_troll_template)} строк.")
    try:
        await update.message.delete()
    except:
        pass

# -----------------------
# /troll — быстрая “лесенка”
# -----------------------
async def troll_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global troll_stop, saved_troll_template
    if update.effective_user.id != OWNER_ID:
        return
    if not saved_troll_template:
        return await update.message.reply_text("❌ Нет шаблона. Используй /trollsave.")
    troll_stop = False
    try:
        await update.message.delete()
    except:
        pass
    chat_id = update.effective_chat.id
    for line in saved_troll_template:
        if troll_stop:
            break
        try:
            await context.bot.send_message(chat_id=chat_id, text=line)
        except Exception as e:
            print("Ошибка /troll:", e)
        await asyncio.sleep(0.02)
    if not troll_stop:
        await context.bot.send_message(chat_id=chat_id, text="✅ Троллинг завершён 💞")

# -----------------------
# /trollstop
# -----------------------
async def trollstop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global troll_stop
    if update.effective_user.id != OWNER_ID:
        return
    troll_stop = True
    await update.message.reply_text("🛑 Троллинг остановлен!")

# -----------------------
# /all — рассылка
# -----------------------
async def all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    text = re.sub(r'^/all\s+', '', update.message.text).strip()
    if not text:
        return await update.message.reply_text("❌ Введи текст: /all <текст>")
    count = 0
    for chat_id in list(last_messages.keys()):
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
            count += 1
            await asyncio.sleep(0.05)
        except:
            continue
    await update.message.reply_text(f"✅ Рассылка завершена ({count} чатов).")

# -----------------------
# /love — проверка совместимости
# -----------------------
async def love_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bot_active:
        return
    args = update.message.text.split(maxsplit=1)
    initiator = update.effective_user.username or update.effective_user.first_name
    target = args[1].replace("@", "") if len(args) > 1 else initiator
    score = random.randint(0, 100)
    bars = "❤️" * (score // 10) + "🖤" * (10 - score // 10)
    phrase = random.choice(LOVE_PHRASES + LOVE_JOKES)
    level = next((lbl for lo, hi, lbl in LOVE_LEVELS if lo <= score <= hi), "")
    await update.message.reply_text(
        f"💞 @{initiator} 💖 @{target}\n"
        f"Совместимость: {score}% [{bars}]\n"
        f"{phrase}\n{level}"
    )

# -----------------------
# /gift — подарок
# -----------------------
async def gift_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bot_active:
        return
    args = update.message.text.split(maxsplit=1)
    if len(args) < 2:
        return await update.message.reply_text("🎁 Используй: /gift @username")
    giver = update.effective_user.username or update.effective_user.first_name
    target = args[1].replace("@", "")
    gift = random.choice(GIFTS_ROMANTIC + GIFTS_FUNNY)
    await update.message.reply_text(f"🎁 @{giver} дарит @{target} подарок:\n{gift}")

# -----------------------
# Логирование сообщений
# -----------------------
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        last_messages[update.message.chat.id] = update.message.chat.id
    if not bot_active:
        return  # не отвечает, если выключен

# -----------------------
# Запуск
# -----------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("onbot", onbot))
    app.add_handler(CommandHandler("offbot", offbot))
    app.add_handler(CommandHandler("trollsave", trollsave_cmd))
    app.add_handler(CommandHandler("troll", troll_cmd))
    app.add_handler(CommandHandler("trollstop", trollstop_cmd))
    app.add_handler(CommandHandler("all", all_cmd))
    app.add_handler(CommandHandler("love", love_cmd))
    app.add_handler(CommandHandler("gift", gift_cmd))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_messages))

    print("✅ Love+Troll Bot запущен!")
    app.run_polling()
