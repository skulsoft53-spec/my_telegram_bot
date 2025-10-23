import os
import threading
import asyncio
import random
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
last_messages = {}  # chat_id -> chat_id

# -----------------------
# ❤️ Данные LoveBot
# -----------------------
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

GIFS_LIST = [
    "https://media.giphy.com/media/3o6ZsY6N0g5cN6E8sQ/giphy.gif",
    "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
    "https://media.giphy.com/media/26ufdipQqU2lhNA4g/giphy.gif"
]

# -----------------------
# 🌐 Мини-вебсервер
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
# ⚙️ Помощник для сохранения чатов
# -----------------------
async def save_chat(update: Update):
    if update.effective_chat:
        last_messages[update.effective_chat.id] = update.effective_chat.id

# -----------------------
# ⚙️ /start — только в ЛС
# -----------------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type != "private":
        return
    await save_chat(update)
    await update.message.reply_text(
        "💞 Привет! Я LoveBot 💖\n"
        "Команды:\n"
        "/love <@username> — проверить совместимость 💘\n"
        "/gift <@username> — отправить подарок 🎁\n"
        "/onbot /offbot — включить/выключить бота (только владелец)\n"
        "/all <текст> — рассылка всем (только владелец)"
    )

# -----------------------
# 💌 /love
# -----------------------
async def love_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update)
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

        await update.message.reply_text("💘 Определяем уровень любви...")
        await asyncio.sleep(0.5)

        atmosphere = random.choice([
            "✨ Судьба соединяет сердца...",
            "💞 Любовь витает в воздухе...",
            "🌹 Сердца бьются всё чаще...",
            "🔥 Между вами искра...",
        ])
        await context.bot.send_message(chat_id=update.effective_chat.id, text=atmosphere)
        await asyncio.sleep(0.7)

        result_text = f"💞 @{initiator} 💖 @{target}\n💘 Совместимость: {score}%\n[{bars}]"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=result_text)
        await asyncio.sleep(0.5)

        category = next((lbl for (lo, hi, lbl) in LOVE_LEVELS if lo <= score <= hi), "💞 Нежные чувства")
        phrase = random.choice(LOVE_PHRASES + LOVE_JOKES + SPECIAL_PHRASES)
        final_text = f"💖 *{category}*\n🌸 {phrase}\n💬 Истинная любовь всегда найдёт путь 💫"
        await context.bot.send_message(chat_id=update.effective_chat.id, text=final_text, parse_mode="Markdown")
        await send_log(context, f"/love: @{initiator} -> @{target} = {score}%")
    except Exception as e:
        print("Ошибка /love:", e)
        await send_log(context, f"Ошибка /love: {e}")

# -----------------------
# 🎁 /gift
# -----------------------
async def gift_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update)
    if update.message is None or not bot_active:
        return
    args = update.message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.message.reply_text("🎁 Используй: /gift @username")
        return
    giver = update.effective_user.username or update.effective_user.first_name
    target = args[1].replace("@", "")
    gift_text = random.choice(GIFS_LIST)
    await update.message.reply_text(f"🎁 @{giver} дарит @{target} гифку:\n{gift_text}")
    await send_log(context, f"/gift: @{giver} -> @{target} ({gift_text})")

# -----------------------
# /all
# -----------------------
async def all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update)
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Только владелец может использовать /all")
        return
    text = update.message.text.partition(" ")[2].strip()
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
# 💬 Обработка сообщений
# -----------------------
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await save_chat(update)
    if not bot_active:
        return

# -----------------------
# 🌟 Фоновая задача — случайная GIF каждые 5 минут
# -----------------------
async def auto_gifs(app: ApplicationBuilder):
    await asyncio.sleep(10)  # старт через 10 секунд
    while True:
        if last_messages:
            chat_id = random.choice(list(last_messages.keys()))
            gif = random.choice(GIFS_LIST)
            try:
                await app.bot.send_message(chat_id=chat_id, text=f"💌 Сюрприз-гивка для тебя!\n{gif}")
            except Exception:
                pass
        await asyncio.sleep(300)  # каждые 5 минут

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
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_messages))

    # Запуск фоновой задачи через loop бота
    app.create_task(auto_gifs(app))

    print("✅ LoveBot с GIF запущен!")
    app.run_polling()
