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
bot_active = True
last_messages = {}

# 🔒 Ограничение одновременных задач
MAX_CONCURRENT_TASKS = 10
task_semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

# 📌 Хранение шаблона для троллинга
saved_troll_template = None
troll_stop = False

# 💖 Полный список фраз для троллинга
TROLL_WORDS = [
    "Ты мне дорог", "Я рад, что ты есть", "Ты особенная", "Ты мой человек",
    "С тобой спокойно", "Ты просто счастье", "Ты делаешь день лучше", "Ты важна",
    "Ты мой уют", "Ты как свет", "Ты делаешь меня лучше", "С тобой всё по-другому",
    "Ты моя радость", "Ты мой светлый человек", "Ты моё вдохновение", "Ты просто прекрасна",
    "Ты мой свет в любой день", "Ты человек, которого не заменить", "Ты моё всё", "Ты дыхание моих чувств",
    "Ты часть моего мира", "Ты нежность моего сердца", "Ты моё утро и мой покой", "Ты чудо, подаренное судьбой",
    "Ты наполняешь жизнь смыслом", "Ты мой покой в шумном мире", "С тобой хочется жить",
    "Ты делаешь меня счастливым", "Ты — моё настоящее", "Ты — лучшее, что со мной случалось",
    "Ты как солнце после дождя", "Ты даришь тепло даже молчанием", "Ты — моя гармония", "Ты — мой дом",
    "Ты всегда в моих мыслях", "Ты — причина моего вдохновения", "Ты приносишь свет туда, где темно",
    "Ты — мой самый нежный человек", "Ты даёшь мне силы", "Ты — мой уют и покой", "С тобой всё имеет смысл",
    "Ты наполняешь меня радостью", "Ты — мой смысл", "Ты — человек, которого хочется беречь",
    "Ты — счастье, о котором я не просил, но получил", "Ты — мой тихий рай", "Ты — мой день и моя ночь",
    "Ты — нежность, в которой хочется остаться", "Ты — самая добрая часть моего сердца",
    "Ты делаешь жизнь ярче", "Ты — человек, с которым хочется всё", "Ты — мой вдохновитель",
    "Ты — человек, ради которого стоит жить", "Ты — мой внутренний свет", "Ты — моё спокойствие в этом мире",
    "Ты — мечта, ставшая реальностью", "Ты — самое тёплое чувство во мне",
    "Ты — человек, которому можно доверить сердце", "Ты — мой нежный шторм",
    "Ты — человек, рядом с которым всё становится возможным", "Ты — мой самый ценный человек",
    "Ты — причина моего счастья", "Ты — человек, с которым время останавливается",
    "Ты — мой нежный свет", "Ты — человек, которого я не хочу терять", "Ты — дыхание моей души",
    "Ты — человек, который делает мир красивее", "Ты — моё вдохновение и покой одновременно",
    "Ты — нежность, которой не хватает этому миру", "Ты — человек, без которого день неполный",
    "Ты — моя самая добрая мысль",
    "С тобой даже тишина звучит красиво 💫",
    "Ты — причина улыбки Апачи 💖",
    "Когда ты рядом, весь мир добрее 🌸",
    "Ты — вдохновение Апачи 💞",
    "Ты — свет, в котором он живёт ☀️",
    "Ты — чувство, которое невозможно описать словами 💓",
    "Апачи просто видит в тебе особенное 🌹",
    "Ты — тот человек, ради которого хочется быть лучше 💫",
    "Ты — искренность, которую он ценит 💖",
    "Полюби Апачи, как он тебя 💞"
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
        "/trollsave — сохранить шаблон 📝\n"
        "/troll — печать шаблона лесенкой 🪜 (только владелец)\n"
        "/trollstop — остановка троллинга 🛑\n"
        "/on и /off — включить/выключить бота (только создатель)."
    )

# 💾 /trollsave
async def trollsave_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global saved_troll_template
    if update.message.from_user.username != OWNER_USERNAME:
        await update.message.reply_text("🚫 Только владелец может использовать эту команду.")
        return
    saved_troll_template = "\n".join(TROLL_WORDS)
    await update.message.reply_text(f"✅ Шаблон для троллинга сохранён. Количество строк: {len(TROLL_WORDS)}")

# 🪜 /troll — печать лесенкой
async def troll_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global troll_stop
    if update.message.from_user.username != OWNER_USERNAME:
        await update.message.reply_text("🚫 Только владелец может использовать эту команду.")
        return
    if not saved_troll_template:
        await update.message.reply_text("❌ Нет сохранённого шаблона. Используй /trollsave")
        return

    async def send_ladder():
        global troll_stop
        async with task_semaphore:
            troll_stop = False
            message = update.message
            lines = saved_troll_template.split("\n")
            typed_text = ""
            for line in lines:
                if troll_stop:
                    await message.reply_text("🛑 Троллинг остановлен.")
                    return
                typed_text += line + "\n"
                try:
                    await message.edit_text(typed_text)
                except:
                    await message.reply_text(typed_text)
                await asyncio.sleep(0.1)

    asyncio.create_task(send_ladder())

# 🛑 /trollstop — остановка троллинга
async def trollstop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global troll_stop
    if update.message.from_user.username != OWNER_USERNAME:
        await update.message.reply_text("🚫 Только владелец может использовать эту команду.")
        return
    troll_stop = True
    await update.message.reply_text("🛑 Команда остановки активирована.")

# 🚀 Запуск бота
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("trollsave", trollsave_command))
    app.add_handler(CommandHandler("troll", troll_command))
    app.add_handler(CommandHandler("trollstop", trollstop_command))
    print("🚀 Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
