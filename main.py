import os
import threading
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import random

# 🔑 Токен
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Ошибка: переменная окружения TELEGRAM_TOKEN не установлена!")
print("✅ TELEGRAM_TOKEN найден, бот запускается...")

# ⚙️ Настройки
SIGNATURE_USER = "Habib471"
SIGNATURE_TEXT = "Полюби Апачи, как он тебя 💞"
OWNER_USERNAME = "bxuwy"
bot_active = True

# 🔒 Ограничение одновременных задач
MAX_CONCURRENT_TASKS = 10
task_semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

# 💖 Романтические фразы (для /love)
LOVE_PHRASES = [
    "Ты мне дорог",
    "Я рад, что ты есть",
    "Ты особенная",
    "Ты мой человек",
    "С тобой спокойно",
    "Ты просто счастье",
    "Ты делаешь день лучше",
    "Каждый миг с тобой бесценен",
    "Ты моя радость и вдохновение",
    "С тобой хочется мечтать и жить",
    "Ты — свет в моей жизни",
    "Каждое утро начинается с мысли о тебе",
    "Ты делаешь всё вокруг ярче",
    "С тобой любое место становится домом",
    "Ты — моя маленькая вселенная",
]

SPECIAL_PHRASES = [
    "С тобой даже тишина звучит красиво 💫",
    "Ты — причина улыбки Апачи 💖",
    "Ты — вдохновение Апачи 💞",
    "Твои глаза — как океан, в котором хочется тонуть",
    "С тобой каждый момент становится магией",
    "Ты — музыка моего сердца",
    "Твои слова — как ласковый ветер в душе",
    "Твоя улыбка способна растопить лёд в сердце",
    "Ты — самая прекрасная мелодия в моей жизни",
    "С тобой даже дождь кажется волшебным",
]

LOVE_LEVELS = [
    (0, 10, "💔 Лёд между сердцами... но всё ещё есть шанс."),
    (11, 25, "🌧️ Едва заметная искра, но она может вспыхнуть."),
    (26, 45, "💫 Симпатия растёт, пусть время покажет."),
    (46, 65, "💞 Нежное притяжение между вами."),
    (66, 80, "💖 Сердца начинают биться в унисон."),
    (81, 95, "💘 Это почти любовь — искренняя и сильная."),
    (96, 100, "💍 Судьба связала вас — любовь навсегда."),
]

GIFTS_ROMANTIC = [
    "💐 Букет слов и немного нежности",
    "🍫 Шоколад из чувства симпатии",
    "🌹 Роза с ароматом тишины",
    "💌 Сердце, написанное от руки",
    "☕ Кофе с привкусом заботы",
    "🌙 Ночь под звёздами для двоих",
    "💖 Улыбка, которая лечит душу",
    "🎶 Мелодия из воспоминаний",
]

GIFTS_FUNNY = [
    "🍕 Один кусочек любви и три крошки заботы",
    "🍟 Картошку с соусом симпатии",
    "🧸 Игрушку, чтобы не скучать",
    "🪄 Волшебную палочку, чтобы день был добрее",
    "🎈 Воздушный шарик с теплом",
    "🕶️ Каплю стиля и горсть обаяния",
    "🍰 Кусочек счастья, свежеиспечённый!",
    "🐸 Лягушку удачи (вдруг принц?)",
]

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

# 💬 Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💞 Привет! Я LoveBot by Apachi.\n"
        "Команды:\n"
        "/love — проверить совместимость 💘\n"
        "/gift — подарить подарок 🎁\n"
        "/onbot — включить бота 🔔 (только владелец)\n"
        "/offbot — отключить бота на обновление 🔕 (только владелец)"
    )

async def bot_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if update.message.from_user.username != OWNER_USERNAME:
        await update.message.reply_text("🚫 У тебя нет прав использовать эту команду.")
        return
    bot_active = True
    await update.message.reply_text("🔔 Бот включен!")

async def bot_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if update.message.from_user.username != OWNER_USERNAME:
        await update.message.reply_text("🚫 У тебя нет прав использовать эту команду.")
        return
    bot_active = False
    await update.message.reply_text("🔕 Бот отключен на обновление!")

# 💘 /love
async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if not bot_active:
        await update.message.reply_text("⏳ Бот сейчас отключен на обновление. Попробуй позже.")
        return

    async def process_love():
        async with task_semaphore:
            message = update.message
            target = message.text.split(maxsplit=1)[1] if len(message.text.split()) > 1 else message.from_user.username
            final_score = random.randint(0, 100)
            phrase = random.choice(SPECIAL_PHRASES if target.lower() == SIGNATURE_USER.lower() else LOVE_PHRASES)
            category = next((label for (low, high, label) in LOVE_LEVELS if low <= final_score <= high), "💞 Нежные чувства")
            bar_length = 10
            filled_length = final_score * bar_length // 100
            bar = "❤️" * filled_length + "🖤" * (bar_length - filled_length)
            result_text = f"💞 @{message.from_user.username} 💖 @{target}\n{final_score}% [{bar}]\n{phrase}\nКатегория: {category}"
            if target.lower() == SIGNATURE_USER.lower():
                result_text += f"\n\n{SIGNATURE_TEXT}"
            await message.reply_text(result_text)
    asyncio.create_task(process_love())

# 🎁 /gift
async def gift_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if not bot_active:
        await update.message.reply_text("⏳ Бот сейчас отключен на обновление. Попробуй позже.")
        return

    async def process_gift():
        async with task_semaphore:
            message = update.message
            args = message.text.split(maxsplit=1)
            if len(args) < 2:
                await message.reply_text("🎁 Используй: /gift @username")
                return
            target = args[1].replace("@", "")
            gift_list = GIFTS_ROMANTIC if random.choice([True, False]) else GIFTS_FUNNY
            gift = random.choice(gift_list)
            await message.reply_text(f"🎁 @{message.from_user.username} дарит @{target} подарок:\n{gift}")
    asyncio.create_task(process_gift())

# 🚀 Запуск
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("onbot", bot_on))
    app.add_handler(CommandHandler("offbot", bot_off))
    app.add_handler(CommandHandler("love", love_command))
    app.add_handler(CommandHandler("gift", gift_command))
    print("🚀 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
