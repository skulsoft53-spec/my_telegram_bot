import os
import threading
import asyncio
import random
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 🔑 Токен
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Ошибка: TELEGRAM_TOKEN не установлен!")

print("✅ TELEGRAM_TOKEN найден, бот запускается...")

# ⚙️ Настройки
OWNER_ID = 8486672898
LOG_CHANNEL_ID = -1003107269526
bot_active = True
updating = False
last_messages = {}
saved_troll_template = None
troll_stop = False

# 🌐 Мини-сервер для Render
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
        print(f"Ошибка лога: {e}")

# ⚙️ Команды включения/выключения
async def bot_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if update.message is None or update.message.from_user.id != OWNER_ID:
        return
    bot_active = False
    await update.message.reply_text("⚠️ Бот отключён. Отвечает только на команды.")

async def bot_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if update.message is None or update.message.from_user.id != OWNER_ID:
        return
    bot_active = True
    await update.message.reply_text("🔔 Бот снова активен!")

# 💾 Сохранение шаблона для троллинга
async def trollsave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global saved_troll_template
    if update.message is None or update.message.from_user.id != OWNER_ID:
        return

    args = update.message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.message.reply_text("❌ Введи текст: /trollsave <текст>")
        return

    text = args[1].strip()

    # если уже есть переносы строк — сохраняем их
    if "\n" in text:
        saved_troll_template = text.split("\n")
    else:
        # умное разбиение по словам (каждые 6 слов)
        words = text.split()
        saved_troll_template = []
        for i in range(0, len(words), 6):
            saved_troll_template.append(" ".join(words[i:i+6]))

    await update.message.reply_text("✅ Шаблон сохранён!")
    await update.message.delete()

# 🪜 Быстрый троллинг (новое сообщение на каждую строку)
async def troll(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global troll_stop
    if update.message is None or update.message.from_user.id != OWNER_ID:
        return

    if not saved_troll_template:
        await update.message.reply_text("❌ Нет сохранённого шаблона. Используй /trollsave.")
        return

    troll_stop = False
    await update.message.delete()

    chat_id = update.message.chat.id
    for line in saved_troll_template:
        if troll_stop:
            break
        try:
            await context.bot.send_message(chat_id=chat_id, text=line)
        except Exception:
            continue
        await asyncio.sleep(0.01)  # скорость отправки

# 🛑 Остановка троллинга
async def trollstop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global troll_stop
    if update.message is None or update.message.from_user.id != OWNER_ID:
        return
    troll_stop = True
    await update.message.reply_text("🛑 Троллинг остановлен!")

# 📣 /all — сообщение всем
async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.message.from_user.id != OWNER_ID:
        return
    text = re.sub(r'^/all\s+', '', update.message.text, flags=re.I).strip()
    if not text:
        await update.message.reply_text("❌ Введи текст для рассылки.")
        return
    for chat_id in list(last_messages.keys()):
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
        except Exception:
            continue
    await update.message.reply_text("✅ Рассылка завершена.")

# 💬 Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    last_messages[update.message.chat.id] = update.message.chat.id

    # если бот выключен — не реагирует на обычные сообщения
    if not bot_active and not update.message.text.startswith("/"):
        return

# 🚀 Запуск
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # Команды
    app.add_handler(MessageHandler(filters.Regex(r'^/onbot$'), bot_on))
    app.add_handler(MessageHandler(filters.Regex(r'^/offbot$'), bot_off))
    app.add_handler(MessageHandler(filters.Regex(r'^/trollsave'), trollsave))
    app.add_handler(MessageHandler(filters.Regex(r'^/troll$'), troll))
    app.add_handler(MessageHandler(filters.Regex(r'^/trollstop$'), trollstop))
    app.add_handler(MessageHandler(filters.Regex(r'^/all'), all_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("✅ Бот запущен и готов к троллингу!")
    app.run_polling()
