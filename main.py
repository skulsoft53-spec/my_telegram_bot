import os
import random
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# Бот отвечает только этому пользователю:
TARGET_USERNAME = "@Habib471"

# Вероятность ответа (0.4 = 40%)
RESPONSE_CHANCE = 0.4

# Поэтичные романтичные фразы с эмодзи 💞
LOVE_PHRASES = [
    "Ты — как утро после долгой ночи, тихая и тёплая 🌅",
    "Когда ты улыбаешься, весь мир будто становится добрее 💞",
    "В каждом дыхании моих мыслей живёшь ты 💫",
    "Ты — свет, что не гаснет даже в самые тёмные дни 🌙",
    "Если бы слова могли касаться, я бы обнял тебя каждым из них 💌",
    "Ты — музыка моего сердца, нежная и бесконечная 🎵",
    "Твоё имя — как шёпот весны в сердце 🌸",
    "Ты наполняешь тишину смыслом, а мою душу — светом ☀️",
    "С тобой даже ветер поёт о любви 💗",
    "Ты — мой самый красивый случай в жизни 💕",
    "Твои глаза — мой самый любимый закат 🌅",
    "Ты — строчка, написанная судьбой о нежности ✨",
    "Ты согреваешь даже тогда, когда молчишь 💭",
    "С каждым днём я всё больше понимаю, что без тебя не могу 💞",
    "Ты — вдох, после которого не хочется выдыхать 💖",
    "Каждое твоё слово оставляет след в моём сердце 🌷",
    "Ты — как звезда, что освещает мою вселенную 💫",
    "С любовью к тебе всё стало яснее, светлее, тише 💌",
    "Ты — мой смысл, мой покой и моё чудо 💗",
    "Если бы любовь имела имя — она звалась бы тобой 💞",
]

# Возможные подписи от Апачи
SIGNATURES = [
    "Апачи тебя любит ❤️",
    "С любовью, твой Апачи 💞",
    "Ты в сердце Апачи навсегда 💗",
    "Полюби Апачи, как он тебя 🌙",
    "От Апачи с теплом 💌",
]

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.from_user:
        return

    # Проверяем: сообщение от нужного пользователя и в группе
    if message.chat.type in ["group", "supergroup"] and message.from_user.username == TARGET_USERNAME[1:]:
        if random.random() <= RESPONSE_CHANCE:
            phrase = random.choice(LOVE_PHRASES)
            signature = random.choice(SIGNATURES)
            response = f"{phrase}\n\n{signature}"
            await message.reply_text(response)

def main():
    BOT_TOKEN = os.environ.get("8456574639:AAH29cxmqD-aQxHRZFZijYBaqjRWbiAEM_w")
    if not BOT_TOKEN:
        print("❌ Ошибка: переменная BOT_TOKEN не найдена.")
        return

    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.ALL, handle_message))
    print("💞 LoveBot by Apachi запущен и ждёт сообщений...")
    app.run_polling()

if __name__ == "__main__":
    main()