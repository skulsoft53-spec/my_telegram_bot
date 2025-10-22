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
# 🔑 Конфигурация
# -----------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Ошибка: TELEGRAM_TOKEN не установлен!")

OWNER_ID = 8486672898
LOG_CHANNEL_ID = -1003107269526
bot_active = True

# Хранилище
last_messages = {}  # chat_id -> chat_id (для /all)

# Тексты для /love и /gift
LOVE_PHRASES = [
    "Ты мне дорог", "Я рад, что ты есть", "Ты особенная", "Ты мой человек",
    "С тобой спокойно", "Ты просто счастье", "Ты делаешь день лучше", "Ты важна",
    "Ты мой уют", "Ты как свет", "Ты делаешь меня лучше", "С тобой всё по-другому",
    "Ты моя радость", "Ты моё вдохновение", "Ты просто прекрасна", "Ты моё всё",
]
SPECIAL_PHRASES = [
    "С тобой даже тишина звучит красиво 💫",
    "Ты — причина чьей-то улыбки 💖",
]
LOVE_JOKES = ["Ты как Wi-Fi — рядом, и всё идеально 😄"]
LOVE_LEVELS = [
    (0, 10, "💔 Лёд между сердцами... но всё ещё есть шанс."),
    (11, 25, "🌧️ Едва заметная искра."),
    (26, 45, "💫 Симпатия растёт."),
    (46, 65, "💞 Нежное притяжение."),
    (66, 80, "💖 Сердца бьются в унисон."),
    (81, 95, "💘 Это почти любовь."),
    (96, 100, "💍 Судьба связала вас — любовь навсегда."),
]
GIFTS_ROMANTIC = ["💐 Букет слов и немного нежности", "🍫 Шоколад из чувства симпатии"]
GIFTS_FUNNY = ["🍕 Один кусочек любви и три крошки заботы", "🍟 Картошка с соусом симпатии"]

# -----------------------
# Мини-вебсервер (Render)
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
# Вспомогательные
# -----------------------
async def send_log(context: ContextTypes.DEFAULT_TYPE, text: str):
    try:
        if context and context.bot:
            await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=text)
    except Exception:
        print("LOG:", text)

# -----------------------
# /love — супер эффект с лесенкой и мигающими сердцами
# -----------------------
async def love_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or not bot_active:
        return
    try:
        args = update.message.text.split(maxsplit=1)
        initiator = update.effective_user.username or update.effective_user.first_name
        target = args[1].replace("@", "") if len(args) > 1 else initiator
        score = random.randint(0, 100)

        # Базовые символы
        hearts = ["❤️", "💖", "💘", "💞", "💝", "❣️"]
        sparkles = ["✨", "💫", "🌸", "⭐"]
        bar_len = 20

        # стартовое сообщение
        msg = await update.message.reply_text(f"💞 @{initiator} 💖 @{target}\n[{''.join(['🖤']*bar_len)}] 0%")

        # Диагональная лесенка
        for step in range(bar_len):
            line = " " * step + random.choice(hearts + sparkles) * (bar_len - step)
            percent = step * 100 // bar_len
            text = f"💞 @{initiator} 💖 @{target}\n{line} {percent}%"

            # каждая 3-я строка — романтическая фраза
            if step % 3 == 0:
                phrase = random.choice(LOVE_PHRASES + LOVE_JOKES + SPECIAL_PHRASES)
                text += f"\n{phrase}"

            try:
                await msg.edit_text(text)
            except Exception:
                pass
            await asyncio.sleep(0.12)

        # Финальная пульсация
        for _ in range(6):
            line = "".join(random.choice(hearts + sparkles) for _ in range(bar_len))
            phrase = random.choice(LOVE_PHRASES + LOVE_JOKES + SPECIAL_PHRASES)
            category = next((lbl for (lo, hi, lbl) in LOVE_LEVELS if lo <= score <= hi), "💞 Нежные чувства")
            final_text = f"💞 @{initiator} 💖 @{target}\n{line}\n{phrase}\n\nКатегория: {category}"
            try:
                await msg.edit_text(final_text)
            except Exception:
                pass
            await asyncio.sleep(0.25)

        await send_log(context, f"/love: @{initiator} -> @{target} = {score}%")

    except Exception as e:
        print("Ошибка /love:", e)
        await send_log(context, f"Ошибка /love: {e}")

# -----------------------
# /gift — подарок
# -----------------------
async def gift_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or not bot_active:
        return
    args = update.message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.message.reply_text("🎁 Используй: /gift @username")
        return
    giver = update.effective_user.username or update.effective_user.first_name
    target = args[1].replace("@", "")
    gift = random.choice(GIFTS_ROMANTIC if random.choice([True, False]) else GIFTS_FUNNY)
    msg = await update.message.reply_text(f"🎁 @{giver} дарит @{target} подарок:\n🎁 …")
    for _ in range(2):
        await asyncio.sleep(0.15)
        try:
            await msg.edit_text(f"🎁 @{giver} дарит @{target} подарок:\n🎁 🎉")
        except Exception:
            pass
    try:
        await msg.edit_text(f"🎁 @{giver} дарит @{target} подарок:\n{gift}")
    except Exception:
        pass
    await send_log(context, f"/gift: @{giver} -> @{target} ({gift})")

# -----------------------
# /all — рассылка
# -----------------------
async def all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user.id != OWNER_ID:
        return
    text = re.sub(r'^/all\s+', '', update.message.text, flags=re.I).strip()
    if not text:
        await update.message.reply_text("❌ Введи текст: /all <текст>")
        return
    count = 0
    for chat_id in list(last_messages.keys()):
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
            count += 1
            await asyncio.sleep(0.02)
        except Exception:
            continue
    await update.message.reply_text(f"✅ Рассылка завершена, отправлено в ~{count} чатов.")
    await send_log(context, f"/all: отправлено в {count} чатов.")

# -----------------------
# Включение / выключение бота
# -----------------------
async def onbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if update.message is None or update.effective_user.id != OWNER_ID:
        return
    bot_active = True
    await update.message.reply_text("🔔 Бот снова активен!")
    await send_log(context, "Бот включён.")

async def offbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if update.message is None or update.effective_user.id != OWNER_ID:
        return
    bot_active = False
    await update.message.reply_text("⚠️ Бот отключён — отвечает только на команды.")
    await send_log(context, "Бот отключён.")

# -----------------------
# Логирование сообщений
# -----------------------
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    last_messages[update.message.chat.id] = update.message.chat.id

# -----------------------
# Запуск бота
# -----------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # команды
    app.add_handler(CommandHandler("onbot", onbot))
    app.add_handler(CommandHandler("offbot", offbot))
    app.add_handler(CommandHandler("love", love_cmd))
    app.add_handler(CommandHandler("gift", gift_cmd))
    app.add_handler(CommandHandler("all", all_cmd))

    # логирование всех текстов
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_messages))

    print("✅ Love Bot с вау-эффектом запущен!")
    app.run_polling()
