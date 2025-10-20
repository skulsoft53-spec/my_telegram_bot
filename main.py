import os
import random
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# Пользователь, которому бот отвечает на каждое сообщение
TARGET_USERNAMES = ["Habib471"]

# Все романтические фразы 💞
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
    "С тобой даже ветер дышит любовью 🌬️",
    "Ты — причина улыбаться без причины 💕",
    "Твоё имя звучит как нежная песня 💖",
    "Ты — светлая мысль во всех моих днях 🌤️",
    "Когда ты рядом, всё остальное теряет значение 🌺",
    "Ты — мой дом, где покой и тепло 🕊️",
    "Каждая встреча с тобой — маленькое чудо ✨",
    "Ты — утренний луч в моём сердце 🌞",
    "С тобой даже звёзды сияют ярче 🌟",
    "Ты — капля любви в океане жизни 💧",
    "Ты — вдох, без которого не дышу 💫",
    "В твоих глазах — целая вселенная нежности 🌌",
    "Ты — слово ‘счастье’, написанное светом 💕",
    "Ты — мой якорь и мой полёт одновременно 💞",
    "Ты — мой уют даже в самых холодных днях ❄️",
    "Твоё присутствие делает этот мир мягче 🌸",
    "Ты — улыбка судьбы, которую я не хочу терять 💫",
    "Ты — аромат весны в моих мыслях 🌼",
    "С тобой мир обретает рифму и музыку 🎵",
    "Ты — мой лучик в мире сумраков 🌙",
    "Ты — нежность, обретшая форму 💗",
    "Каждое утро с тобой — праздник души 🌅",
    "Ты — тепло, что не уходит даже зимой 🔥",
    "Ты — мой смысл и моя простая радость 💞",
    "С тобой даже дождь поёт о любви 🌧️",
    "Ты — мгновение, которое хочется повторять 💖",
    "Ты — сладкий сон, который не хочется прерывать 🌙",
    "Ты — вдохновение каждой строки 💫",
    "Ты — мой маяк в океане чувств 🌊",
    "Ты — мягкий свет, что ведёт сквозь тьму 🌠",
    "Ты — чудо, к которому не перестаю тянуться 💗",
    "Ты — дыхание радости в каждом дне 💕",
    "Ты — отклик сердца на зов любви 💌",
    "Ты — нежный огонь в холодном мире 🔥",
    "С тобой даже молчание становится стихом 🌸",
    "Ты — моя самая красивая случайность 💫",
    "Ты — свет в каждом взгляде 💖",
    "Ты — утро, которое не хочется отпускать 🌅",
    "Ты — причина моего вдоха и улыбки 💞",
    "С тобой всё просто и всё по-настоящему ☀️",
    "Ты — мой стих, написанный звёздами 🌠",
    "Ты — прикосновение света к душе 💫",
    "Ты — песня, что звучит без слов 🎶",
    "Ты — дыхание тепла в моём сердце 💗",
    "Ты — улыбка, за которой скрыто солнце ☀️",
    "Ты — мой внутренний покой 🌙",
    "Ты — как лето в сердце зимой 🌺",
    "Ты — светлая нота моего дня 🎵",
    "Ты — мой нежный маяк в буре жизни 🌊",
    "Ты — шепот, что лечит душу 💞",
    "Ты — моя бесконечность в одном взгляде 💫",
    "Ты — смысл, что делает всё остальное ненужным 💖",
    "Ты — мой ангел среди людей 🕊️",
    "Ты — дыхание счастья 💗",
    "Ты — как стих, который хочется перечитывать 🌸",
    "Ты — улыбка, согревающая сердце 💞",
    "Ты — вдохновение моего вдоха 💫",
    "Ты — мечта, к которой ведут все пути 🌠",
    "Ты — нежность, обернутая в свет 🌷",
    "Ты — мой рассвет и мой закат одновременно 🌅",
    "Ты — мой ответ на все вопросы 💌",
    "Ты — чудо, о котором я молчал 💖",
    "Ты — нежность, что живёт в каждом мгновении 💞",
    "Ты — дыхание весны в холодном дне 🌸",
    "Ты — тепло, спрятанное в моих мыслях ☀️",
    "Ты — мой любимый хаос 💫",
    "Ты — поцелуй судьбы, оставшийся навсегда 💕",
    "Ты — вдохновение каждой капли дождя 🌧️",
    "Ты — огонь, что не обжигает 🔥",
    "Ты — тайна, которую не хочу разгадать 💌"
]

# Подписи
SIGNATURES = [
    "Апачи тебя любит ❤️",
    "Ты в сердце Апачи навсегда 💗",
    "Полюби Апачи, как он тебя 🌙",
    "От Апачи с теплом 💌",
]

# Мини-веб-сервер Render
def run_web():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write("LoveBot is running on Render <3".encode("utf-8"))

    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💞 Привет! Я LoveBot by Apachi.\n"
        "Я буду отвечать на каждое сообщение @Habib471 💌\n"
        "Командой /love вы можете проверить совместимость с любым пользователем!"
    )

# Ответ на сообщения выбранного пользователя
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.from_user:
        return

    username = message.from_user.username
    if message.chat.type in ["group", "supergroup"] and username in TARGET_USERNAMES:
        phrase = random.choice(LOVE_PHRASES)
        signature = random.choice(SIGNATURES)
        response = f"{phrase}\n\n{signature}"
        await message.reply_text(response, reply_to_message_id=message.message_id)

# Команда /love для всех
async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not context.args or len(context.args) == 0:
        await message.reply_text("❌ Укажи пользователя, например: /love @username")
        return

    target_username = context.args[0].lstrip('@')
    user1 = message.from_user.username or message.from_user.first_name
    user2 = target_username

    # Случайная совместимость
    score = random.randint(50, 100)
    phrase = random.choice(LOVE_PHRASES)
    signature = random.choice(SIGNATURES)

    await message.reply_text(
        f"💖 Совместимость {user1} и {user2}: {score}% 💖\n\n{phrase}\n{signature}"
    )

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
