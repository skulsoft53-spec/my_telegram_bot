import os
import threading
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
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
LOG_CHANNEL_ID = -1003107269526
bot_active = True
updating = False
last_messages = {}
MAX_CONCURRENT_TASKS = 10
task_semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

# 📌 Троллинг
saved_troll_template = None
troll_stop = False

# 💖 Фразы love
LOVE_PHRASES = [
    "Ты мне дорог", "Я рад, что ты есть", "Ты особенная", "Ты мой человек",
    "С тобой спокойно", "Ты просто счастье", "Ты делаешь день лучше", "Ты важна",
    "Ты мой уют", "Ты как свет", "Ты делаешь меня лучше", "С тобой всё по-другому",
    "Ты моя радость", "Ты мой светлый человек", "Ты моё вдохновение", "Ты просто прекрасна",
    "Ты мой свет в любой день", "Ты человек, которого не заменить", "Ты моё всё",
]
SPECIAL_PHRASES = [
    "С тобой даже тишина звучит красиво 💫",
    "Ты — причина улыбки Апачи 💖",
]
LOVE_JOKES = ["Ты как Wi-Fi — рядом, и всё идеально 😄"]
LOVE_LEVELS = [
    (0, 10, "💔 Лёд между сердцами... но всё ещё есть шанс."),
    (11, 25, "🌧️ Едва заметная искра, но она может вспыхнуть."),
    (26, 45, "💫 Симпатия растёт, пусть время покажет."),
    (46, 65, "💞 Нежное притяжение между вами."),
    (66, 80, "💖 Сердца начинают биться в унисон."),
    (81, 95, "💘 Это почти любовь — искренняя и сильная."),
    (96, 100, "💍 Судьба связала вас — любовь навсегда."),
]
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
        "💞 Привет! Я LoveBot by Apachi.\n"
        "Команды:\n"
        "/love — проверить совместимость 💘\n"
        "/gift — подарить подарок 🎁\n"
        "/trollsave — сохранить шаблон 📝\n"
        "/troll — печать шаблона лесенкой 🪜 (только владелец)\n"
        "/trollstop — остановка троллинга 🛑\n"
        "/onbot /offbot — включить/выключить бота (только создатель)\n"
        "/all <текст> — отправка всем (только владелец)"
    )

async def bot_off_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    global bot_active, updating
    if update.message.from_user.username != OWNER_USERNAME:
        await update.message.reply_text("🚫 Только владелец.")
        return
    bot_active = False
    updating = True
    await update.message.reply_text("⚠️ Бот отключен — он теперь отвечает только на команды.")
    await send_log(context, "Бот отключен на обновление.")

async def bot_on_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    global bot_active, updating
    if update.message.from_user.username != OWNER_USERNAME:
        await update.message.reply_text("🚫 Только владелец.")
        return
    bot_active = True
    updating = False
    await update.message.reply_text("🔔 Бот снова активен!")
    await send_log(context, "Бот включен.")

# 💘 love
async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or not bot_active:
        return
    async with task_semaphore:
        message = update.message
        args = message.text.split(maxsplit=1)
        target = args[1].replace("@", "") if len(args) > 1 else message.from_user.username
        final_score = random.randint(0, 100)
        hearts = ["❤️", "💖", "💘", "💞"]
        sparkles = ["✨", "💫", "🌸", "⭐"]
        bar_length = 20
        filled_length = final_score * bar_length // 100
        bar = "".join(random.choices(hearts + sparkles, k=filled_length)) + "🖤" * (bar_length - filled_length)
        sent_msg = await message.reply_text(f"💞 @{message.from_user.username} 💖 @{target}\n{final_score}% [{bar}]")
        for _ in range(3):
            anim_bar = "".join(random.choices(hearts + sparkles, k=filled_length)) + "🖤" * (bar_length - filled_length)
            await sent_msg.edit_text(f"💞 @{message.from_user.username} 💖 @{target}\n{final_score}% [{anim_bar}]")
            await asyncio.sleep(0.2)
        phrase = random.choice(SPECIAL_PHRASES if target.lower() == SIGNATURE_USER.lower() else LOVE_PHRASES + LOVE_JOKES)
        category = next((label for (low, high, label) in LOVE_LEVELS if low <= final_score <= high), "💞 Нежные чувства")
        result_text = f"💞 @{message.from_user.username} 💖 @{target}\n🎯 Результат: {final_score}% [{bar}]\n{phrase}\n\nКатегория: {category}"
        if target.lower() == SIGNATURE_USER.lower():
            result_text += f"\n\n{SIGNATURE_TEXT}"
        await sent_msg.edit_text(result_text)
        await send_log(context, f"love: @{message.from_user.username} 💖 @{target} = {final_score}%")

# 🎁 gift
async def gift_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or not bot_active:
        return
    async with task_semaphore:
        message = update.message
        args = message.text.split(maxsplit=1)
        if len(args) < 2:
            await message.reply_text("🎁 Используй: /gift @username")
            return
        target = args[1].replace("@", "")
        gift_list = GIFTS_ROMANTIC if random.choice([True, False]) else GIFTS_FUNNY
        gift = random.choice(gift_list)
        sent_msg = await message.reply_text(f"🎁 @{message.from_user.username} дарит @{target} подарок:\n🎁 …")
        for _ in range(3):
            await asyncio.sleep(0.2)
            await sent_msg.edit_text(f"🎁 @{message.from_user.username} дарит @{target} подарок:\n🎁 🎉")
        await sent_msg.edit_text(f"🎁 @{message.from_user.username} дарит @{target} подарок:\n{gift}")
        await send_log(context, f"gift: @{message.from_user.username} → @{target} ({gift})")

# 💾 trollsave
async def trollsave_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global saved_troll_template
    if update.message is None or update.message.from_user.username != OWNER_USERNAME:
        return
    args = update.message.text.split(maxsplit=1)
    if len(args) < 2:
        return
    text = args[1].strip()
    if "\n" in text:
        saved_troll_template = text.split("\n")
    else:
        max_len = 40
        saved_troll_template = [text[i:i+max_len] for i in range(0, len(text), max_len)]
    await update.message.delete()

# 🪜 troll
async def troll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global troll_stop
    if update.message is None or update.message.from_user.username != OWNER_USERNAME:
        return
    if not saved_troll_template:
        return
    await update.message.delete()
    troll_stop = False

    async def send_ladder():
        global troll_stop
        for line in saved_troll_template:
            if troll_stop:
                break
            await context.bot.send_message(chat_id=update.message.chat.id, text=line)
            await asyncio.sleep(0.05)

    asyncio.create_task(send_ladder())

# 🛑 trollstop
async def trollstop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global troll_stop
    if update.message is None or update.message.from_user.username != OWNER_USERNAME:
        return
    troll_stop = True
    await update.message.reply_text("🛑 Троллинг остановлен!")

# /all
async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.from_user.username != OWNER_USERNAME:
        return
    text = re.sub(r'^/all\s+', '', update.message.text, flags=re.I).strip()
    if not text:
        await update.message.reply_text("❌ Текст для отправки не указан.")
        return
    async with task_semaphore:
        for chat_id in list(last_messages.keys()):
            try:
                await context.bot.send_message(chat_id=chat_id, text=text)
            except Exception:
                continue

# 💬 Логирование сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    last_messages[update.message.chat.id] = update.message.chat.id
    # Если бот выключен, не отвечаем на обычные сообщения, только на команды
    if not bot_active and not update.message.text.startswith("/"):
        return

# 🚀 Запуск
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.Regex(r'^/start$'), start))
    app.add_handler(MessageHandler(filters.Regex(r'^/onbot$'), bot_on_command))
    app.add_handler(MessageHandler(filters.Regex(r'^/offbot$'), bot_off_command))
    app.add_handler(MessageHandler(filters.Regex(r'^/love'), love_command))
    app.add_handler(MessageHandler(filters.Regex(r'^/gift'), gift_command))
    app.add_handler(MessageHandler(filters.Regex(r'^/trollsave'), trollsave_command))
    app.add_handler(MessageHandler(filters.Regex(r'^/troll$'), troll_command))
    app.add_handler(MessageHandler(filters.Regex(r'^/trollstop$'), trollstop_command))
    app.add_handler(MessageHandler(filters.Regex(r'^/all'), all_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("✅ Бот запущен!")
    app.run_polling()
