import os
import threading
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import random

# 🔑 Токен
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Ошибка: переменная окружения TELEGRAM_TOKEN не установлена!")
print("✅ TELEGRAM_TOKEN найден, бот запускается...")

# ⚙️ Настройки
TARGET_USERNAMES = ["Habib471"]
SIGNATURE_USER = "Habib471"
SIGNATURE_TEXT = "Полюби Апачи, как он тебя 💞"
OWNER_USERNAME = "bxuwy"
LOG_CHANNEL_ID = -1003107269526

bot_active = True
updating = False
last_messages = {}

# 🔒 Ограничение одновременных задач
MAX_CONCURRENT_TASKS = 10
task_semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

# 📌 Троллинг
saved_troll_template = None
troll_stop = False

# 💖 Романтические слова для /love
LOVE_PHRASES = [
    "Ты мне дорог", "Я рад, что ты есть", "Ты особенная", "Ты мой человек",
    "С тобой спокойно", "Ты просто счастье", "Ты делаешь день лучше", "Ты важна",
    "Ты мой уют", "Ты как свет", "Ты делаешь меня лучше", "С тобой всё по-другому",
    "Ты моя радость", "Ты мой светлый человек", "Ты моё вдохновение", "Ты просто прекрасна",
    "Ты мой свет в любой день", "Ты человек, которого не заменить", "Ты моё всё", "Ты дыхание моих чувств"
]

SPECIAL_PHRASES = [
    "С тобой даже тишина звучит красиво 💫",
    "Ты — причина улыбки Апачи 💖"
]

LOVE_JOKES = ["Ты как Wi-Fi — рядом, и всё идеально 😄"]

GIFTS_ROMANTIC = ["💐 Букет слов и немного нежности", "🍫 Шоколад из чувства симпатии"]
GIFTS_FUNNY = ["🍕 Один кусочек любви и три крошки заботы", "🍟 Картошку с соусом симпатии"]

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
        "/trollsave — сохранить шаблон 📝\n"
        "/troll — печать шаблона лесенкой 🪜 (только владелец)\n"
        "/trollstop — остановка троллинга 🛑\n"
        "/onbot и /offbot — включить/выключить бота"
    )

async def bot_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active, updating
    if update.message.from_user.username != OWNER_USERNAME:
        await update.message.reply_text("🚫 У тебя нет прав использовать эту команду.")
        return
    bot_active = True
    updating = False
    await update.message.reply_text("🔔 Бот включен!")

async def bot_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active, updating
    if update.message.from_user.username != OWNER_USERNAME:
        await update.message.reply_text("🚫 У тебя нет прав использовать эту команду.")
        return
    bot_active = False
    updating = True
    await update.message.reply_text("🔕 Бот выключен на обновление!")

# 💘 /love
async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bot_active:
        if updating:
            await update.message.reply_text("⚠️ Бот временно отключен на обновление.")
        return

    async def process_love():
        async with task_semaphore:
            message = update.message
            args = message.text.split(maxsplit=1)
            target = args[1].replace("@", "") if len(args) > 1 else message.from_user.username
            final_score = random.randint(0, 100)
            phrase = random.choice(SPECIAL_PHRASES if target.lower() == SIGNATURE_USER.lower() else LOVE_PHRASES + LOVE_JOKES)
            sent_msg = await message.reply_text(f"💞 @{message.from_user.username} 💖 @{target}\n0% [----------]")
            bar_length = 10
            filled_length = final_score * bar_length // 100
            bar = "❤️" * filled_length + "🖤" * (bar_length - filled_length)
            await sent_msg.edit_text(f"💞 @{message.from_user.username} 💖 @{target}\n{final_score}% [{bar}]")
            result_text = f"💞 @{message.from_user.username} 💖 @{target}\nРезультат: {final_score}%\n{phrase}"
            if target.lower() == SIGNATURE_USER.lower():
                result_text += f"\n\n{SIGNATURE_TEXT}"
            await sent_msg.edit_text(result_text)

            # Лог в канал
            await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=f"/love: @{message.from_user.username} -> @{target}, {final_score}%")

    asyncio.create_task(process_love())

# 🎁 /gift
async def gift_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bot_active:
        if updating:
            await update.message.reply_text("⚠️ Бот временно отключен на обновление.")
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
            await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=f"/gift: @{message.from_user.username} -> @{target}, подарок: {gift}")

    asyncio.create_task(process_gift())

# 💾 /trollsave
async def trollsave_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global saved_troll_template
    if update.message.from_user.username != OWNER_USERNAME:
        await update.message.reply_text("🚫 Только владелец может использовать эту команду.")
        return
    args = update.message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.message.reply_text("❌ Используй: /trollsave <текст с \\n>")
        return
    saved_troll_template = args[1].split("\\n")
    await update.message.reply_text(f"✅ Шаблон сохранён с {len(saved_troll_template)} строками.")

# 🪜 /troll
async def troll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global troll_stop
    if update.message.from_user.username != OWNER_USERNAME:
        await update.message.reply_text("🚫 Только владелец может использовать эту команду.")
        return
    if not saved_troll_template:
        await update.message.reply_text("❌ Нет сохранённого шаблона. Используй /trollsave <текст>")
        return

    async def send_ladder():
        global troll_stop
        async with task_semaphore:
            troll_stop = False
            for line in saved_troll_template:
                if troll_stop:
                    break
                await update.message.reply_text(line)
                await asyncio.sleep(0.1)
            await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=f"/troll выполнен владельцем @{update.message.from_user.username}")

    asyncio.create_task(send_ladder())

# 🛑 /trollstop
async def trollstop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global troll_stop
    if update.message.from_user.username != OWNER_USERNAME:
        await update.message.reply_text("🚫 Только владелец может использовать эту команду.")
        return
    troll_stop = True
    await update.message.reply_text("🛑 Троллинг остановлен.")

# 🚀 Запуск
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("onbot", bot_on))
    app.add_handler(CommandHandler("offbot", bot_off))
    app.add_handler(CommandHandler("love", love_command))
    app.add_handler(CommandHandler("gift", gift_command))
    app.add_handler(CommandHandler("trollsave", trollsave_command))
    app.add_handler(CommandHandler("troll", troll_command))
    app.add_handler(CommandHandler("trollstop", trollstop_command))
    print("🚀 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
