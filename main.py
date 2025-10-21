import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes
import random

# Токен
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Ошибка: переменная окружения TELEGRAM_TOKEN не установлена!")
print("✅ TELEGRAM_TOKEN найден, бот запускается...")

# Настройки
TARGET_USERNAMES = ["Habib471"]
SIGNATURE_USER = "Habib471"
SIGNATURE_TEXT = "Полюби Апачи, как он тебя"
bot_active = True
last_messages = {}
users_sent_messages = set()

# Все романтические фразы + шутки
LOVE_PHRASES = [
    "Ты — моё вдохновение, дыхание весны 🌸",
    "С тобой каждый день — маленькое чудо ✨",
    "Ты — моя мелодия счастья 🎶",
    "В твоих глазах вижу небо и свет 🌌",
    "Каждое слово твоё — ветерок в душе 🍃",
    "С тобой тишина звучит как музыка 🎵",
    "Ты — дыхание света в сердце 💖",
    "Когда ты рядом, мир мягче 🌈",
    "Ты — утренний луч, озаряющий душу ☀️",
    "С тобой каждый момент — страница сказки 📖",
    "Ты — капля любви в океане жизни 🌊",
    "В твоей улыбке спрятан целый мир 🌹",
    "Ты — мой якорь и полёт одновременно ⚓️🕊️",
    "Каждое утро с тобой — праздник души 🎉",
    "Ты — мягкий свет, что ведёт сквозь тьму 💡",
    "С тобой каждая минута превращается в волшебство ✨",
    "Ты — смысл, делающий всё остальное второстепенным 🫶",
    "С тобой даже дождь кажется музыкой 🌧️🎶",
    "Ты — моя бесконечность в одном взгляде ♾️",
    "Ты — утренний рассвет, озаряющий жизнь ☀️",
    "С тобой серые дни становятся яркими 🌈",
    "Ты — песня, которую хочется слушать бесконечно 🎵",
    "Каждое прикосновение твоей руки — шёпот счастья 🤲",
    "Ты — мой маяк в буре жизни 🗼",
    "С тобой хочется создавать маленькие чудеса 🪄",
    "Ты — аромат весны в мыслях 🌸",
    "Когда ты смеёшься, мир кажется идеальным 😄",
    "Ты — мягкий свет среди сумрака 🌟",
    "С тобой я чувствую себя целым 🧩",
    "Ты — любимая случайность, ставшая смыслом 💞",
    "Каждое твоё слово — строчка поэмы 📝",
    "Ты — вдохновение в моменты сомнений 💫",
    "С тобой хочется лететь, даже если ноги не касаются земли 🕊️",
    "Ты — тихая радость, согревающая сердце 💖",
    "Когда ты рядом, мир дышит в унисон 🌬️",
    "Ты — шёпот счастья в тишине 🤫",
    "С тобой я учусь видеть красоту в каждом мгновении 🌷",
    "Ты — нежность, превращающая обыденность в чудо 🌟",
    "Каждое утро с тобой — первый вдох после сна 🌅",
    "Ты — лучик света, рассекающий мрак 🌞",
    "С тобой жизнь обретает ритм 🎵",
    "Ты — тихая гавань в шумном мире ⛵",
    "Каждое движение твоё — танец вселенной 💃",
    "Ты — вдохновение, превращающее мысли в поэзию ✍️",
    "С тобой даже молчание звучит как музыка 🎶",
    "Ты — мой космос, полный светлых звёзд 🌌",
    "Когда ты рядом, время замирает ⏳",
    "Ты — тёплое облако в холодном мире ☁️",
    "С тобой простые слова обретают смысл 📝",
    "Ты — утренний кофе, без которого день не начинается ☕",
    "Каждое твоё «привет» — солнечный луч 🌞",
    "Ты — тихая музыка, звучащая только для меня 🎶",
    "С тобой хочется мечтать и верить 🌈",
    "Ты — лёгкость, растворяющая заботы 🌬️",
    "Каждое дыхание твоё — новая жизнь для души 🌸",
    "Ты — мягкий свет в сердце 💡",
    "С тобой мир становится ярче 🌈",
    "Ты — узор счастья в повседневности 🎨",
    "Когда смотришь на меня, вижу вселенную 🌌",
    "Ты — уют даже в пасмурные дни 🏡",
    "С тобой каждый день похож на сказку 🪄",
    "Ты — любимая глава книги моей жизни 📖",
    "Каждое слово твоё — ласковое прикосновение 🤲",
    "Ты — свет, превращающий тьму в рассвет 🌅",
    "С тобой ощущаю гармонию 🌿",
    "Ты — вечная весна в сердце 🌸",
    "Каждое мгновение с тобой — драгоценность 💎",
    "Ты — тихая радость среди шума 🌟",
    "С тобой дождь — симфония 🌧️🎶",
    "Ты — компас в жизни 🧭",
    "Когда рядом, хочется улыбаться без причины 😄",
    "Ты — шелест листвы в сердце 🍃",
    "С тобой хочу идти по жизни за руку 🤝",
    "Ты — вдохновляющая тишина 🌌",
    "Каждое прикосновение твоё — сияние солнца ☀️",
    "Ты — шёпот, лечащий сомнения 🌸",
    "С тобой хочется творить и мечтать 🌈",
    "Ты — смысл, делающий жизнь настоящей 💖",
    "Когда смеёшься, мир добрее 😊",
    "Ты — тихая гавань и буря одновременно 🌊",
    "С тобой каждый день — красивая история 📖",
    "Ты — мягкое прикосновение света 🌟",
    "Каждое слово твоё — мелодия счастья 🎵",
    "Ты — утренний рассвет и вечерняя звезда 🌅⭐",
    "С тобой хочется быть лучше 🌸",
    "Ты — бесконечная мечта 💫",
    "Когда рядом, кажется, что всё возможно 🌈",
    "Ты — нежность, делающая мир мягче 💖",
    "С тобой хочется останавливаться в моменте ⏳",
    "Ты — маленькое чудо каждый день 🌟",
    "Каждое мгновение с тобой — дыхание радости 💓",
    "Ты — музыка, что волнует сердце 🎶",
    "С тобой обычный день становится волшебным ✨",
    "Ты — мягкий свет в душе навсегда 🌞",
    "Ты — вдохновляющая сказка 📖",
    "С тобой мир обретает новые цвета 🌈",
    "Ты — тихий океан тепла и спокойствия 🌊",
    "Каждое движение твоё — танец вселенной 💃",
    "Ты — гармония, превращающая хаос в смысл 🌟",
    "С тобой ощущаю вечность ⏳",
    "Ты — лучик света, никогда не гаснет 💡",
    "С тобой хочется любить и творить бесконечно 💞",
    "Ты — маяк через трудности жизни 🗼",
    "Когда смотришь, вижу всё ценное 🌌",
    "Ты — шелест счастья в сердце 🍃",
    "С тобой учусь радоваться каждому мгновению 🌸",
    "Ты — вдохновение, оживляющее мысли ✍️",
]

LOVE_JOKES = [
    "Ты как Wi-Fi — рядом, и всё идеально 😄",
    "Ты — батарейка, без тебя теряю заряд 🔋",
    "Если бы ты был кофе, не просыпался бы без тебя ☕",
    "Ты как пароль: сложный, но жизнь без тебя невозможна 🔑",
    "Ты — любимая песня на повторе 🎶",
]

# Веб-сервер
def run_web():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"LoveBot is running <3")
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💞 Привет! Я LoveBot by Apachi.\n"
        "Я реагирую на выбранных пользователей 💌\n"
        "Команда /love покажет все романтические фразы ✨\n"
        "Команды /on и /off включают и выключают бота."
    )

async def bot_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    bot_active = True
    await update.message.reply_text("🔔 Бот включен!")

async def bot_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    bot_active = False
    await update.message.reply_text("🔕 Бот выключен!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bot_active:
        return
    message = update.message
    if not message or not message.from_user:
        return
    username = message.from_user.username
    users_sent_messages.add(username)
    if message.chat.type in ["group", "supergroup"]:
        if username in TARGET_USERNAMES:
            phrase = random.choice(LOVE_PHRASES + LOVE_JOKES)
            last_messages[username] = phrase
            text_to_send = phrase
            if username == SIGNATURE_USER:
                text_to_send += f"\n\n{SIGNATURE_TEXT}"
            await message.reply_text(text_to_send, reply_to_message_id=message.message_id)

# Команда /love
async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bot_active:
        return
    message = update.message
    args = message.text.split(maxsplit=1)
    target = args[1] if len(args) > 1 else message.from_user.username

    score = random.randint(0, 100)
    all_phrases = "\n".join(LOVE_PHRASES + LOVE_JOKES)
    text_to_send = f"💌 Совместимость с {target}: {score}%\n\n{all_phrases}"

    if target == SIGNATURE_USER:
        text_to_send += f"\n\n{SIGNATURE_TEXT}"

    await message.reply_text(text_to_send)

# Главная функция
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("love", love_command))
    app.add_handler(CommandHandler("on", bot_on))
    app.add_handler(CommandHandler("off", bot_off))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("🚀 Бот запущен и работает!")
    app.run_polling()

if __name__ == "__main__":
    main()
