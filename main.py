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
last_messages = {}

# ❤️ Романтические данные
LOVE_PHRASES = [
    "Ты мне дорог", "Я рад, что ты есть", "Ты особенная",
    "Ты мой человек", "Ты делаешь день лучше", "Ты просто счастье",
    "Ты как свет в тумане", "Ты вдохновляешь", "Ты важна для меня",
    "Ты мое чудо", "Ты наполняешь день теплом", "Ты моя радость",
    "С тобой спокойно", "Ты просто невероятна", "Ты мой уют", "Ты моё всё"
]
SPECIAL_PHRASES = [
    "С тобой даже тишина звучит красиво 💫",
    "Ты — причина чьей-то улыбки 💖",
]
LOVE_JOKES = [
    "Ты как Wi-Fi — рядом, и всё идеально 😄",
    "Ты как Telegram Premium — недостижима, но прекрасна 💎",
]
LOVE_LEVELS = [
    (0, 10, "💔 Лёд между сердцами..."),
    (11, 25, "🌧️ Едва заметная искра."),
    (26, 45, "💫 Симпатия растёт."),
    (46, 65, "💞 Нежное притяжение."),
    (66, 80, "💖 Сердца бьются в унисон."),
    (81, 95, "💘 Это почти любовь."),
    (96, 100, "💍 Судьба связала вас навсегда."),
]

GIFTS_ROMANTIC = [
    "💐 Букет слов и немного нежности",
    "🍫 Шоколад из чувства симпатии",
    "🌹 Цветы и нежные объятия",
    "💌 Романтическое послание с сердцем"
]
GIFTS_FUNNY = [
    "🍕 Один кусочек любви и три крошки заботы",
    "🍟 Картошка с соусом симпатии",
    "🎁 Мешок смеха и хорошего настроения"
]

# -----------------------
# 🌐 Мини-вебсервер (Render)
# -----------------------
def run_web():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write("LoveBot is alive 💖".encode("utf-8"))

    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()

# -----------------------
# 📜 Логирование
# -----------------------
async def send_log(context: ContextTypes.DEFAULT_TYPE, text: str):
    try:
        if context and context.bot:
            await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=text)
    except Exception:
        print("LOG:", text)

# -----------------------
# ⚙️ Команды включения/выключения
# -----------------------
async def onbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Только владелец может включать бота.")
        return
    bot_active = True
    await update.message.reply_text("🔔 Бот снова активен!")
    await send_log(context, "Бот включён.")

async def offbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Только владелец может выключать бота.")
        return
    bot_active = False
    await update.message.reply_text("⚠️ Бот отключён. Отвечает только на команды.")
    await send_log(context, "Бот отключён.")

# -----------------------
# /start — только в ЛС
# -----------------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    await update.message.reply_text(
        "💞 Привет! Я LoveBot 💖\n"
        "Команды:\n"
        "/love — проверить совместимость 💘\n"
        "/gift — подарить подарок 🎁\n"
        "/onbot /offbot — включить/выключить бота (только создатель)\n"
        "/all <текст> — отправка всем (только владелец)"
    )

# -----------------------
# /love — эффектная версия
# -----------------------
async def love_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or not bot_active:
        return
    try:
        args = update.message.text.split(maxsplit=1)
        initiator = update.effective_user.username or update.effective_user.first_name
        target = args[1].replace("@", "") if len(args) > 1 else initiator

        score = random.randint(0, 100)
        bar_len = 20
        filled = score * bar_len // 100
        hearts = "❤️" * (filled // 2)
        bars = hearts + "🖤" * (bar_len - len(hearts))

        # Вступление
        await update.message.reply_text("💘 Определяем уровень любви...")
        await asyncio.sleep(0.5)

        # Атмосфера
        atmosphere = random.choice([
            "✨ Судьба соединяет сердца...",
            "💞 Любовь витает в воздухе...",
            "🌹 Сердца бьются всё чаще...",
            "🔥 Между вами искра...",
        ])
        await context.bot.send_message(chat_id=update.effective_chat.id, text=atmosphere)
        await asyncio.sleep(0.7)

        # Результат
        result_text = (
            f"💞 @{initiator} 💖 @{target}\n"
            f"💘 Совместимость: {score}%\n"
            f"[{bars}]"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=result_text)
        await asyncio.sleep(0.5)

        # Финал с эмоциями
        category = next((lbl for (lo, hi, lbl) in LOVE_LEVELS if lo <= score <= hi), "💞 Нежные чувства")
        phrase = random.choice(LOVE_PHRASES + LOVE_JOKES + SPECIAL_PHRASES)
        final_text = (
            f"💖 *{category}*\n"
            f"🌸 {phrase}\n"
            f"💬 Истинная любовь всегда найдёт путь 💫"
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=final_text,
            parse_mode="Markdown"
        )
        await send_log(context, f"/love: @{initiator} -> @{target} = {score}%")
    except Exception as e:
        print("Ошибка /love:", e)
        await send_log(context, f"Ошибка /love: {e}")

# -----------------------
# /gift — эффектная версия
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
# /all — рассылка по сохранённым чатам
# -----------------------
async def all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Только владелец может использовать /all")
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
    await update.message.reply_text(f"✅ Рассылка завершена, отправлено в {count} чатов.")
    await send_log(context, f"/all: отправлено в {count} чатов.")

# -----------------------
# Логирование чатов
# -----------------------
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat:
        last_messages[update.effective_chat.id] = update.effective_chat.id
    if not bot_active:
        return

# -----------------------
# 🚀 Запуск
# -----------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Команды
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("onbot", onbot))
    app.add_handler(CommandHandler("offbot", offbot))
    app.add_handler(CommandHandler("love", love_cmd))
    app.add_handler(CommandHandler("gift", gift_cmd))
    app.add_handler(CommandHandler("all", all_cmd))

    # Логирование всех сообщений
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_messages))

    print("✅ LoveBot запущен и готов к романтике 💞")
    app.run_polling()
