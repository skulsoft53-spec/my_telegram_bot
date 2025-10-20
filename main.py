import os
import random
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# ------------------------
# Пользователи
# ------------------------
TARGET_USERNAMES = ["Habib471"]       # Романтика
NEGATIVE_USERNAMES = ["vkhich1ro"]    # Негатив

# ------------------------
# Романтические фразы 💞
# ------------------------
LOVE_PHRASES = [
    "Ты — моё вдохновение, нежное как дыхание весны 🌷",
    "С тобой всё вокруг наполняется смыслом 💫",
    "Ты — моя мелодия счастья, тихая и вечная 🎶",
    "В каждом луче солнца я вижу твой свет ☀️",
    "Ты — шёпот нежности в шуме мира 🌸",
    "Каждая мысль о тебе — как утренний рассвет 🌅",
    "С тобой даже тишина звучит прекраснее 💞",
    "Ты — дыхание света в моём сердце ✨",
    "В твоих глазах спрятано небо и тепло 🌌",
    "Ты — мечта, которая стала реальностью 💗",
    "Ты — моя радость и свет в темноте 🌟",
    "Ты — мягкость в этом жестоком мире 💖",
    "С тобой каждая минута — чудо 💫",
    "Ты — любовь, которую хочется хранить 💕",
    "Ты — нежность, согревающая душу 🌷",
    "Ты — вдохновение моего сердца 💗",
    "Ты — мой свет в конце туннеля 🌅",
    "Ты — музыка в моих мыслях 🎶",
    "Ты — счастье, что стало реальностью 💞",
    "Ты — мечта, воплощённая в жизнь 🌸",
]

# Подписи к романтическим сообщениям
SIGNATURES = [
    "Апачи тебя любит ❤️",
    "Ты в сердце Апачи навсегда 💗",
    "Полюби Апачи, как он тебя 🌙",
    "От Апачи с теплом 💌",
]

# ------------------------
# Жёсткие негативные фразы 😡
# ------------------------
HARD_NEGATIVE_WORDS = [
    "Ты абсолютно ненадёжный и раздражающий человек!",
    "Невозможно терпеть твою бездушную болтовню!",
    "Твоя пустая болтовня утомляет всех вокруг!",
    "Ты постоянно создаёшь хаос и раздражение!",
    "Твоё присутствие — это как серый туман уныния!",
    "Ты — источник всех проблем и неприятностей!",
    "Никакая логика не спасает твою безумную голову!",
    "Ты бездарно тратишь время и чужие нервы!",
    "Твои поступки вызывают только злость и разочарование!",
    "Ты не способен на доброту и честность!",
    "Твоя лживость поражает всех подряд!",
    "Ты несёшь разочарование куда бы ни пошёл!",
    "Невыносимо слушать твою бессмысленную речь!",
    "Ты — настоящая головная боль для всех!",
    "Твои слова только раздражают и оскорбляют!",
    "Ты постоянно создаёшь драму и негатив!",
    "Невозможно понять твою бессмысленную логику!",
    "Ты как чёрная дыра для счастья других!",
    "Твои действия разрушают всё вокруг!",
    "Ты — воплощение хаоса и безразличия!",
    "Ты — источник фрустрации для всех знакомых!",
    "Твоё присутствие портит настроение окружающим!",
    "Ты словно магнит для неприятностей и проблем!",
    "Невозможно терпеть твою самовлюблённость!",
    "Твоя жадность и эгоизм поражают всех!",
    "Ты — причина всех ссор и конфликтов!",
    "Твои слова ранят больше, чем действия!",
    "Ты только создаёшь стресс и тревогу!",
    "Твоя глупость поражает воображение!",
    "Ты — полное разочарование во всех смыслах!",
    "Твои действия постоянно вызывают раздражение!",
    "Ты разрушитель всего позитивного вокруг!",
    "Ты бездарно тратишь чужое время!",
    "Невыносимо находиться рядом с тобой!",
    "Ты как чума для настроения других людей!",
    "Ты превращаешь радость в скуку и грусть!",
    "Твоя безответственность поражает всех!",
    "Ты — постоянный источник хаоса!",
    "Твоя лень и равнодушие раздражают!",
    "Ты — причина всех ошибок команды!",
    "Твои действия лишены смысла и логики!",
    "Ты — токсичная личность для всех знакомых!",
    "Твои шутки неприятны и оскорбительны!",
]

# ------------------------
# Мини-веб-сервер Render
# ------------------------
def run_web():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write("LoveBot is running on Render <3".encode("utf-8"))

    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()

# ------------------------
# /start
# ------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💞 Привет! Я LoveBot by Apachi.\n"
        "Я буду отвечать на каждое сообщение @Habib471 💌\n"
        "Командой /love вы можете проверить совместимость с любым пользователем!"
    )

# ------------------------
# Ответ на сообщения выбранного пользователя
# ------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.from_user:
        return

    username = message.from_user.username
    chat_type = message.chat.type

    # 40% вероятность отвечать
    if random.random() > 0.4:
        return

    # Романтические пользователи
    if username in TARGET_USERNAMES:
        phrase = random.choice(LOVE_PHRASES)
        response = phrase
        if random.random() < 0.3:  # подпись 30%
            response += f"\n\n{random.choice(SIGNATURES)}"
        await message.reply_text(response, reply_to_message_id=message.message_id)

    # Негативные пользователи
    elif username in NEGATIVE_USERNAMES:
        phrase = random.choice(HARD_NEGATIVE_WORDS)
        await message.reply_text(phrase, reply_to_message_id=message.message_id)

# ------------------------
# Команда /love
# ------------------------
async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    text = message.text.strip()
    if len(text.split()) < 2:
        await message.reply_text("❌ Укажи пользователя, например: /love @username")
        return

    target_username = text.split(maxsplit=1)[1].lstrip('@').strip()
    if not target_username:
        await message.reply_text("❌ Укажи правильного пользователя!")
        return

    user1 = message.from_user.username or message.from_user.first_name
    user2 = target_username

    score = random.randint(50, 100)
    phrase = random.choice(LOVE_PHRASES)

    response = f"💖 Совместимость {user1} и {user2}: {score}% 💖\n\n{phrase}"
    if random.random() < 0.3:  # подпись 30%
        response += f"\n\n{random.choice(SIGNATURES)}"

    await message.reply_text(response)

# ------------------------
# Главная функция
# ------------------------
def main():
    BOT_TOKEN = os.environ.get("BOT_TOKEN")
    if not BOT_TOKEN:
        print("❌ Ошибка: переменная BOT_TOKEN не найдена.")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    app.add_handler(CommandHandler("love", love_command))

    print("💞 LoveBot by Apachi запущен и ждёт сообщений...")
    app.run_polling()

if __name__ == "__main__":
    main()
