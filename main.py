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

OWNER_ID = 8486672898
LOG_CHANNEL_ID = -1003107269526
bot_active = True
last_messages = {}

# -----------------------
# Фразы
# -----------------------
LOVE_PHRASES = [
    "Ты мой свет даже в самый тёмный день 💫",
    "С тобой всё кажется проще 💞",
    "Ты заставляешь мир сиять 🌹",
    "С тобой даже тишина звучит как музыка 💖",
    "Ты делаешь каждый день особенным ✨",
    "Ты — мой уют и покой 💐",
    "Твоя улыбка — моё утро 🌸",
    "Ты — причина моего вдохновения 💘",
]
SPECIAL_PHRASES = [
    "Судьба явно что-то замышляет между вами 💞",
    "Когда вы рядом, даже время замирает ⏳",
    "Два сердца, одно биение 💫",
]
LOVE_JOKES = [
    "Ты как Wi-Fi — рядом, и всё идеально 😄",
    "Любовь — это когда батарея садится, а тебе всё равно ❤️‍🔥"
]
LOVE_LEVELS = [
    (0, 10, "💔 Лёд между сердцами..."),
    (11, 25, "🌧️ Едва заметная искра"),
    (26, 45, "💫 Симпатия растёт"),
    (46, 65, "💞 Нежное притяжение"),
    (66, 80, "💖 Сердца бьются в унисон"),
    (81, 95, "💘 Это почти любовь"),
    (96, 100, "💍 Судьба связала вас навсегда"),
]
GIFTS_ROMANTIC = ["💐 Букет нежности", "🍫 Шоколад из чувств"]
GIFTS_FUNNY = ["🍕 Пицца любви", "🍟 Картошка с соусом симпатии"]

# -----------------------
# Мини-вебсервер (Render)
# -----------------------
def run_web():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"LoveBot is alive 💖")
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
# on/off bot
# -----------------------
async def onbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Только владелец.")
        return
    bot_active = True
    await update.message.reply_text("🔔 Бот снова активен!")
    await send_log(context, "Бот включён.")

async def offbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Только владелец.")
        return
    bot_active = False
    await update.message.reply_text("⚠️ Бот отключён — отвечает только на команды.")
    await send_log(context, "Бот отключён.")

# -----------------------
# /love — вау-эффект ❤️
# -----------------------
async def love_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if not bot_active:
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

        # шаг 1
        await update.message.reply_text("💘 Определяем уровень любви...")
        await asyncio.sleep(0.6)

        # шаг 2
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=random.choice([
                "✨ Судьба соединяет сердца...",
                "💞 Любовь витает в воздухе...",
                "🌹 Сердца бьются всё чаще...",
                "🔥 Между вами искра...",
            ])
        )
        await asyncio.sleep(0.7)

        # шаг 3
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"💞 @{initiator} 💖 @{target}\n💘 Совместимость: {score}%\n[{bars}]"
        )
        await asyncio.sleep(0.6)

        # шаг 4 — финал
        category = next((lbl for (lo, hi, lbl) in LOVE_LEVELS if lo <= score <= hi), "💞 Нежные чувства")
        phrase = random.choice(LOVE_PHRASES + LOVE_JOKES + SPECIAL_PHRASES)
        final = (
            f"🌸 *{category}*\n\n"
            f"💬 {phrase}\n\n"
            f"💫 Истинная любовь всегда найдёт путь 💞"
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=final,
            parse_mode="Markdown"
        )

        await send_log(context, f"/love: @{initiator} -> @{target} = {score}%")

    except Exception as e:
        print("Ошибка /love:", e)
        await send_log(context, f"Ошибка /love: {e}")

# -----------------------
# /gift — подарки
# -----------------------
async def gift_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if not bot_active:
        return

    args = update.message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.message.reply_text("🎁 Используй: /gift @username")
        return

    giver = update.effective_user.username or update.effective_user.first_name
    target = args[1].replace("@", "")
    gift = random.choice(GIFTS_ROMANTIC if random.choice([True, False]) else GIFTS_FUNNY)

    await update.message.reply_text(f"🎁 @{giver} дарит @{target} подарок:\n{gift}")
    await send_log(context, f"/gift: @{giver} -> @{target} ({gift})")

# -----------------------
# /all — рассылка
# -----------------------
async def all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
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
    await update.message.reply_text(f"✅ Рассылка завершена, {count} чатов.")
    await send_log(context, f"/all: {count} сообщений")

# -----------------------
# Обработка сообщений
# -----------------------
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    try:
        last_messages[update.message.chat.id] = update.message.chat.id
    except Exception:
        pass
    if not bot_active:
        return

# -----------------------
# Запуск
# -----------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("onbot", onbot))
    app.add_handler(CommandHandler("offbot", offbot))
    app.add_handler(CommandHandler("love", love_cmd))
    app.add_handler(CommandHandler("gift", gift_cmd))
    app.add_handler(CommandHandler("all", all_cmd))

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_messages))

    print("💘 LoveBot запущен и готов творить магию любви!")
    app.run_polling()
