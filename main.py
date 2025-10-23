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
last_messages = {}

# ❤️ Романтика и гифки
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

GIFTS_ROMANTIC = ["💐 Букет слов и немного нежности", "🍫 Шоколад из чувства симпатии"]
GIFTS_FUNNY = ["🍕 Один кусочек любви и три крошки заботы", "🍟 Картошка с соусом симпатии"]

GIFS = {
    "romantic": [
        "https://media.giphy.com/media/3o6Zt6ML6BklcajjsA/giphy.gif",
        "https://media.giphy.com/media/l0MYB8Ory7Hqefo9a/giphy.gif",
    ],
    "funny": [
        "https://media.giphy.com/media/ICOgUNjpvO0PC/giphy.gif",
        "https://media.giphy.com/media/26AHONQ79FdWZhAI0/giphy.gif",
    ]
}

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
# ⚙️ Сохраняем активный чат
# -----------------------
async def save_chat(update: Update):
    if update.effective_chat:
        last_messages[update.effective_chat.id] = update.effective_chat.id

# -----------------------
# ⚙️ Вкл/выкл бота
# -----------------------
async def onbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update)
    global bot_active
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Только владелец может включать бота.")
        return
    bot_active = True
    await update.message.reply_text("🔔 Бот снова активен!")
    await send_log(context, "Бот включён.")

async def offbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update)
    global bot_active
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Только владелец может выключать бота.")
        return
    bot_active = False
    await update.message.reply_text("⚠️ Бот отключён. Отвечает только на команды.")
    await send_log(context, "Бот отключён.")

# -----------------------
# /start — только ЛС
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
# /all — рассылка всем
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
# 🖼 Авто-гифки
# -----------------------
async def auto_gifs(app):
    while True:
        if last_messages and bot_active:
            chat_id = random.choice(list(last_messages.keys()))
            category = random.choice(["romantic", "funny"])
            gif_url = random.choice(GIFS.get(category, GIFS["romantic"]))
            try:
                await app.bot.send_animation(chat_id=chat_id, animation=gif_url)
                await send_log(None, f"Авто-гифка ({category}) отправлена в чат {chat_id}")
            except Exception as e:
                print("Ошибка авто-гифки:", e)
        await asyncio.sleep(random.randint(1800, 5400))

# -----------------------
# 💬 Обработка всех сообщений
# -----------------------
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message:
        await save_chat(update)
    if not bot_active:
        return

# -----------------------
# 🚀 Запуск
# -----------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # команды
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("onbot", onbot))
    app.add_handler(CommandHandler("offbot", offbot))
    app.add_handler(CommandHandler("love", love_cmd))
    app.add_handler(CommandHandler("gift", gift_cmd))
    app.add_handler(CommandHandler("all", all_cmd))

    # логируем текстовые сообщения
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_messages))

    # авто-гифки
    asyncio.create_task(auto_gifs(app))

    print("✅ LoveBot запущен и готов к романтике 💞 и гифкам 🖼")
    app.run_polling()
