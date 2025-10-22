import os
import threading
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes
)
import random
import re

# 🔑 Токен
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Ошибка: переменная окружения TELEGRAM_TOKEN не установлена!")
print("✅ TELEGRAM_TOKEN найден, бот запускается...")

# ⚙️ Настройки
SIGNATURE_USER = "Habib471"
SIGNATURE_TEXT = "Полюби Апачи, как он тебя 💞"
OWNER_USERNAME = "bxuwy"
OWNER_ID = 8486672898
LOG_CHANNEL_ID = -1003107269526

bot_active = True
updating = False
last_messages = {}
MAX_CONCURRENT_TASKS = 10
task_semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)
saved_troll_template = None
troll_stop = False

# 💖 Фразы
LOVE_PHRASES = [
    "Ты мне дорог", "Я рад, что ты есть", "Ты особенная", "Ты мой человек",
    "С тобой спокойно", "Ты просто счастье", "Ты делаешь день лучше", "Ты важна",
    "Ты мой уют", "Ты как свет", "Ты делаешь меня лучше", "С тобой всё по-другому",
    "Ты моя радость", "Ты мой светлый человек", "Ты моё вдохновение", "Ты просто прекрасна",
    "Ты мой свет в любой день", "Ты человек, которого не заменить", "Ты моё всё",
]
SPECIAL_PHRASES = ["С тобой даже тишина звучит красиво 💫", "Ты — причина улыбки Апачи 💖"]
LOVE_JOKES = ["Ты как Wi-Fi — рядом, и всё идеально 😄"]
LOVE_LEVELS = [
    (0, 10, "💔 Лёд между сердцами..."), (11, 25, "🌧️ Едва заметная искра..."),
    (26, 45, "💫 Симпатия растёт..."), (46, 65, "💞 Нежное притяжение..."),
    (66, 80, "💖 Сердца начинают биться в унисон."),
    (81, 95, "💘 Это почти любовь."), (96, 100, "💍 Судьба связала вас.")
]
GIFTS_ROMANTIC = ["💐 Букет слов и немного нежности", "🍫 Шоколад из чувства симпатии"]
GIFTS_FUNNY = ["🍕 Один кусочек любви", "🍟 Картошку с соусом симпатии"]

# 🌐 Мини-сервер
def run_web():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"LoveBot is running <3")
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()

# 📤 Логи
async def send_log(context: ContextTypes.DEFAULT_TYPE, text: str):
    try:
        await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=text)
    except Exception as e:
        print(f"Ошибка при отправке лога: {e}")

# 💬 Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    await update.message.reply_text(
        "💞 Привет! Я LoveBot by Apachi.\n\n"
        "Команды:\n"
        "/love — проверить совместимость 💘\n"
        "/gift — подарить подарок 🎁\n"
        "/trollsave — сохранить шаблон 📝\n"
        "/troll — печать шаблона лесенкой 🪜 (только владелец)\n"
        "/trollstop — остановить троллинг 🛑\n"
        "/onbot /offbot — включить/выключить бота (только создатель)\n"
        "/all <текст> — рассылка всем (только владелец)"
    )

# 🔔 /onbot /offbot
async def bot_on_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active, updating
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Только владелец.")
        return
    bot_active = True
    updating = False
    await update.message.reply_text("🔔 Бот снова активен!")
    await send_log(context, "Бот включён.")

async def bot_off_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active, updating
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Только владелец.")
        return
    bot_active = False
    updating = True
    await update.message.reply_text("⚠️ Бот отключён — теперь отвечает только на команды.")
    await send_log(context, "Бот выключен.")

# 💘 /love
async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bot_active:
        return
    async with task_semaphore:
        msg = update.message
        args = msg.text.split(maxsplit=1)
        target = args[1].replace("@", "") if len(args) > 1 else msg.from_user.username
        score = random.randint(0, 100)
        bar = "❤️" * (score // 5) + "🖤" * (20 - score // 5)
        phrase = random.choice(SPECIAL_PHRASES if target.lower() == SIGNATURE_USER.lower() else LOVE_PHRASES + LOVE_JOKES)
        cat = next((label for (a, b, label) in LOVE_LEVELS if a <= score <= b), "💞 Нежные чувства")
        txt = f"💞 @{msg.from_user.username} 💖 @{target}\n🎯 {score}% [{bar}]\n{phrase}\n\nКатегория: {cat}"
        await msg.reply_text(txt)
        await send_log(context, f"love: @{msg.from_user.username} 💖 @{target} = {score}%")

# 🎁 /gift
async def gift_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bot_active:
        return
    msg = update.message
    args = msg.text.split(maxsplit=1)
    if len(args) < 2:
        await msg.reply_text("🎁 Используй: /gift @username")
        return
    target = args[1].replace("@", "")
    gift = random.choice(GIFTS_ROMANTIC if random.choice([True, False]) else GIFTS_FUNNY)
    await msg.reply_text(f"🎁 @{msg.from_user.username} дарит @{target} подарок:\n{gift}")
    await send_log(context, f"gift: @{msg.from_user.username} → @{target} ({gift})")

# 💾 /trollsave
async def trollsave_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global saved_troll_template
    if update.effective_user.id != OWNER_ID:
        return
    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("❌ Используй: /trollsave <текст>")
        return
    text = parts[1].strip()
    saved_troll_template = [line.strip() for line in text.splitlines() if line.strip()]
    await update.message.reply_text(f"✅ Шаблон сохранён ({len(saved_troll_template)} строк).")

# 🪜 /troll
async def troll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global troll_stop
    if update.effective_user.id != OWNER_ID:
        return
    if not saved_troll_template:
        await update.message.reply_text("❌ Нет шаблона. Используй /trollsave.")
        return

    try:
        await update.message.delete()
    except Exception:
        pass

    troll_stop = False
    msg = await context.bot.send_message(chat_id=update.effective_chat.id, text="\u200b")

    for line in saved_troll_template:
        if troll_stop:
            break
        try:
            await msg.edit_text(line)
        except Exception:
            try:
                await context.bot.send_message(chat_id=update.effective_chat.id, text=line)
            except:
                pass
        await asyncio.sleep(0.01)

# 🛑 /trollstop
async def trollstop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global troll_stop
    if update.effective_user.id != OWNER_ID:
        return
    troll_stop = True
    await update.message.reply_text("🛑 Троллинг остановлен!")

# 📢 /all
async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    text = re.sub(r'^/all\s+', '', update.message.text).strip()
    if not text:
        await update.message.reply_text("❌ Текст не указан.")
        return
    for chat_id in list(last_messages.keys()):
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
        except:
            pass

# 📨 Логирование
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        last_messages[update.message.chat.id] = update.message.chat.id
    if not bot_active:
        return

# 🚀 Запуск
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("onbot", bot_on_command))
    app.add_handler(CommandHandler("offbot", bot_off_command))
    app.add_handler(CommandHandler("love", love_command))
    app.add_handler(CommandHandler("gift", gift_command))
    app.add_handler(CommandHandler("trollsave", trollsave_command))
    app.add_handler(CommandHandler("troll", troll_command))
    app.add_handler(CommandHandler("trollstop", trollstop_command))
    app.add_handler(CommandHandler("all", all_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("✅ Бот запущен!")
    app.run_polling()
