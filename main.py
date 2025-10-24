import os
import threading
import asyncio
import random
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

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

GIFS = [
    "https://media.giphy.com/media/3o6gbbuLW76jkt8vIc/giphy.gif",
    "https://media.giphy.com/media/l4pTfx2qLszoacZRS/giphy.gif",
    "https://media.giphy.com/media/3o7TKPZqzNRejT7Nko/giphy.gif",
    "https://media.giphy.com/media/3oEjI6SIIHBdRxXI40/giphy.gif",
]

GIFTS_ROMANTIC = ["💐 Букет слов и немного нежности", "🍫 Шоколад из чувства симпатии"]
GIFTS_FUNNY = ["🍕 Один кусочек любви и три крошки заботы", "🍟 Картошка с соусом симпатии"]

sent_gifs = set()

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

async def save_chat(update: Update):
    if update.effective_chat:
        last_messages[update.effective_chat.id] = update.effective_chat.id

# -----------------------
# ⚙️ Команды включения/выключения
# -----------------------
async def onbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update)
    global bot_active
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Только владелец может включить бота.")
        return
    bot_active = True
    await update.message.reply_text("🔔 Бот снова активен!")
    await send_log(context, "Бот включён.")

async def offbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update)
    global bot_active
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Только владелец может выключить бота.")
        return
    bot_active = False
    await update.message.reply_text("⚠️ Бот отключён.")
    await send_log(context, "Бот отключён.")

# -----------------------
# /start
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
        "/kiss <@username> — поцелуй или объятие 😘\n"
        "/gif — рандомные гифки 🎬\n"
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
    msg = await update.message.reply_text(f"🎁 @{giver} дарит @{target} подарок...\n🎁 …")
    for _ in range(2):
        await asyncio.sleep(0.15)
        try:
            await msg.edit_text(f"🎁 @{giver} дарит @{target} подарок...\n🎁 🎉")
        except Exception:
            pass
    try:
        await msg.edit_text(f"🎁 @{giver} дарит @{target} подарок:\n{gift}")
    except Exception:
        pass
    await send_log(context, f"/gift: @{giver} -> @{target} ({gift})")

# -----------------------
# 😘 /kiss — поцелуи и объятия + редкий эффект судьбы
# -----------------------
KISS_GIFS = [
    "https://media.giphy.com/media/G3va31oEEnIkM/giphy.gif",
    "https://media.giphy.com/media/11rWoZNpAKw8w/giphy.gif",
    "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif",
    "https://media.giphy.com/media/3o6Zt6ML6BklcajjsA/giphy.gif",
]
HUG_GIFS = [
    "https://media.giphy.com/media/lrr9rHuoJOE0w/giphy.gif",
    "https://media.giphy.com/media/xT9IgG50Fb7Mi0prBC/giphy.gif",
    "https://media.giphy.com/media/3M4NpbLCTxBqU/giphy.gif",
    "https://media.giphy.com/media/BXrwTdoho6hkQ/giphy.gif",
]
RARE_GIFS = [
    "https://media.giphy.com/media/l3vR85PnGsBwu1PFK/giphy.gif",
    "https://media.giphy.com/media/5GoVLqeAOo6PK/giphy.gif",
]

sent_kiss_gifs = set()
sent_hug_gifs = set()

async def kiss_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update)
    if not bot_active or update.message is None:
        return

    args = update.message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.message.reply_text("😘 Используй: /kiss @username — чтобы отправить поцелуй или объятие 💋")
        return

    sender = update.effective_user.username or update.effective_user.first_name
    target = args[1].replace("@", "")

    # 🎆 Редкий шанс судьбы (1 из 20)
    if random.randint(1, 20) == 1:
        rare_gif = random.choice(RARE_GIFS)
        await update.message.reply_text(f"💘 Судьба соединила @{sender} и @{target}! Это редкий момент 💫")
        await asyncio.sleep(0.6)
        await update.message.reply_animation(rare_gif)
        await asyncio.sleep(0.4)
        await context.bot.send_message(chat_id=update.effective_chat.id, text="💞 Пусть ваши сердца всегда будут рядом 💞")
        await send_log(context, f"/kiss RARE: @{sender} -> @{target}")
        return

    action = random.choice(["kiss", "hug"])
    if action == "kiss":
        gifs, sent_set, emoji, text = KISS_GIFS, sent_kiss_gifs, "💋", "поцелуй"
    else:
        gifs, sent_set, emoji, text = HUG_GIFS, sent_hug_gifs, "🤗", "объятие"

    available = list(set(gifs) - sent_set)
    if not available:
        sent_set.clear()
        available = gifs.copy()
    gif = random.choice(available)
    sent_set.add(gif)

    await update.message.reply_text(f"{emoji} @{sender} отправляет @{target} {text}...")
    await asyncio.sleep(0.5)
    await update.message.reply_animation(gif)
    await asyncio.sleep(0.5)
    phrase = random.choice([
        "💞 Между вами пробежала искра нежности!",
        "💖 Любовь витает в воздухе!",
        "🌸 Тепло и нежность переплелись вместе.",
        "💫 Пусть этот момент длится вечно!",
        "🔥 Сердца бьются в унисон.",
    ])
    await context.bot.send_message(chat_id=update.effective_chat.id, text=phrase)
    await send_log(context, f"/kiss: @{sender} -> @{target} ({text})")

# -----------------------
# 🎬 /gif
# -----------------------
async def gif_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await save_chat(update)
    if update.message is None:
        return
    global sent_gifs
    available = list(set(GIFS) - sent_gifs)
    if not available:
        sent_gifs.clear()
        available = GIFS.copy()
    gif = random.choice(available)
    sent_gifs.add(gif)
    await update.message.reply_animation(gif)

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
# 🚀 Запуск
# -----------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("onbot", onbot))
    app.add_handler(CommandHandler("offbot", offbot))
    app.add_handler(CommandHandler("love", love_cmd))
    app.add_handler(CommandHandler("gift", gift_cmd))
    app.add_handler(CommandHandler("kiss", kiss_cmd))
    app.add_handler(CommandHandler("gif", gif_cmd))
    app.add_handler(CommandHandler("all", all_cmd))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), save_chat))

    print("✅ LoveBot запущен и готов к романтике 💞")
    app.run_polling()
