import os
import random
import threading
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# Проверка токена
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Ошибка: переменная окружения TELEGRAM_TOKEN не установлена!")
print("✅ TELEGRAM_TOKEN найден, бот запускается...")

TARGET_USERNAMES = ["Habib471"]
SIGNATURE = "Полюби Апачи, как он тебя"
BOT_ACTIVE = True

# 100 красивых романтических фраз
LOVE_PHRASES = [
    "Ты — моё вдохновение, нежное как дыхание весны.",
    "С тобой каждый день — маленькое чудо.",
    "Ты — моя мелодия счастья.",
    "В твоих глазах я вижу небо.",
    "Каждое твоё слово — как лёгкий ветерок.",
    "С тобой даже тишина звучит прекрасно.",
    "Ты — дыхание света в моём сердце.",
    "Когда ты рядом, мир кажется ярче.",
    "Ты — утренний луч тепла.",
    "С тобой каждый момент — страница в красивой книге.",
    "Ты — капля любви в океане жизни.",
    "В твоей улыбке спрятан целый мир.",
    "Ты — мой якорь и мой полёт одновременно.",
    "Каждое утро с тобой — праздник души.",
    "Ты — мягкий свет, что ведёт меня сквозь тьму.",
    "С тобой каждая минута — волшебство.",
    "Ты — смысл, который делает всё остальное второстепенным.",
    "С тобой даже дождь кажется музыкой.",
    "Ты — мой внутренний покой и буря одновременно.",
    "Ты — моя бесконечность в одном взгляде.",
    "Ты — утренний рассвет, озаряющий мою жизнь.",
    "С тобой даже серые дни становятся яркими.",
    "Ты — песня, которую хочется слушать бесконечно.",
    "Каждое прикосновение твоей руки — счастье.",
    "Ты — мой маяк в буре жизни.",
    "С тобой хочется создавать чудеса каждый день.",
    "Ты — аромат весны в моих мыслях.",
    "Когда ты смеёшься, мир идеален.",
    "Ты — мягкий свет среди сумрака.",
    "С тобой я чувствую себя целым.",
    "Ты — моя любимая случайность.",
    "Каждое твоё слово — как строчка поэмы.",
    "Ты — моё вдохновение в моменты сомнений.",
    "С тобой хочется лететь, даже без земли.",
    "Ты — моя тихая радость.",
    "Когда ты рядом, мир дышит в унисон.",
    "Ты — мягкий шёпот счастья.",
    "С тобой я учусь видеть красоту.",
    "Ты — нежность, превращающая обыденность в чудо.",
    "Каждое утро с тобой — первый вдох после сна.",
    "Ты — лучик света, рассекающий мрак.",
    "С тобой жизнь обретает ритм.",
    "Ты — моя тихая гавань.",
    "Каждое твоё движение — танец вселенной.",
    "Ты — вдохновение, превращающее мысли в поэзию.",
    "С тобой даже молчание звучит как музыка.",
    "Ты — мой космос, полный светлых звёзд.",
    "Когда ты рядом, время замирает.",
    "Ты — тёплое облако в холодном мире.",
    "С тобой даже простые слова обретают смысл.",
    "Ты — мой утренний кофе.",
    "Каждое твоё «привет» — солнечный луч.",
    "Ты — моя тихая музыка.",
    "С тобой хочется мечтать.",
    "Ты — лёгкость, растворяющая тяжесть забот.",
    "Каждое твоё дыхание — новая жизнь для души.",
    "Ты — мягкий свет в моём сердце.",
    "С тобой мир ярче, насыщеннее.",
    "Ты — причудливый узор счастья.",
    "Когда ты смотришь на меня, я вижу вселенную.",
    "Ты — мой уют в холодные дни.",
    "С тобой каждый день — волшебная сказка.",
    "Ты — моя любимая глава в книге жизни.",
    "Каждое твоё слово — ласковое прикосновение.",
    "Ты — свет, превращающий тьму в рассвет.",
    "С тобой ощущаю гармонию.",
    "Ты — вечная весна в сердце.",
    "Каждое мгновение с тобой — драгоценность.",
    "Ты — тихая радость среди мира.",
    "С тобой дождь — симфония.",
    "Ты — компас в жизни.",
    "Когда ты рядом, хочется улыбаться.",
    "Ты — мягкий шелест листвы.",
    "С тобой хочу идти по жизни рука об руку.",
    "Ты — вдохновляющая тишина.",
    "Каждое прикосновение — сияние солнца.",
    "Ты — шёпот, лечащий сомнения.",
    "С тобой хочется творить и жить полной жизнью.",
    "Ты — смысл, делающий жизнь настоящей.",
    "Когда ты смеёшься, мир добрее.",
    "Ты — гавань и буря одновременно.",
    "С тобой каждый день — красивая история.",
    "Ты — мягкое прикосновение света.",
    "Каждое слово — мелодия счастья.",
    "Ты — утренний рассвет и вечерняя звезда.",
    "С тобой хочется быть лучше.",
    "Ты — бесконечная мечта, ставшая явью.",
    "Когда рядом, всё возможно.",
    "Ты — нежность, делающая мир мягче.",
    "С тобой хочется останавливаться в моменте.",
    "Ты — маленькое чудо каждый день.",
    "Каждое мгновение — дыхание радости.",
    "Ты — музыка без слов.",
    "С тобой обычный день — волшебный.",
    "Ты — мягкий свет навсегда.",
    "Ты — вдохновляющая сказка.",
    "С тобой мир обретает новые цвета.",
    "Ты — тихий океан тепла.",
    "Каждое движение — танец вселенной.",
    "Ты — гармония, превращающая хаос в смысл.",
    "С тобой ощущаю вечность.",
    "Ты — лучик света в сердце.",
    "С тобой хочется любить без конца.",
    "Ты — маяк, ведущий через трудности.",
    "Когда смотришь на меня, вижу ценное.",
    "Ты — шелест счастья в сердце.",
    "С тобой учусь радоваться каждому мгновению.",
    "Ты — вдохновение, оживляющее мысли."
]

LOVE_JOKES = [
    "Ты как Wi-Fi — когда рядом, всё работает идеально 😄",
    "Ты — моя батарейка, без тебя теряю заряд ❤️",
    "Если бы ты был кофе, я бы не просыпался без тебя ☕",
    "Ты как пароль: сложный, но без тебя жизнь невозможна 🔑",
    "Ты — моя любимая песня на повторе 🎶",
    "С тобой даже понедельник весёлый 😆",
    "Ты как солнечный день в дождливую погоду 🌞",
    "Ты делаешь жизнь как хороший сериал 🎬",
    "Ты — моя любимая ошибка 😍",
    "Если бы любовь была кодом, я бы компилировал тебя снова 💻",
]

# Мини-веб-сервер
def run_web():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"LoveBot is running <3")
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()

last_messages = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💞 Привет! Я LoveBot by Apachi.\n"
        "Команды: /love, /on, /off\n"
        "Я отвечаю на сообщения выбранных пользователей 💌"
    )

async def turn_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_ACTIVE
    BOT_ACTIVE = True
    await update.message.reply_text("✅ LoveBot включён!")

async def turn_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_ACTIVE
    BOT_ACTIVE = False
    await update.message.reply_text("⛔ LoveBot выключен!")

async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not BOT_ACTIVE:
        return

    user = update.message.from_user
    args = update.message.text.split(maxsplit=1)
    target_name = args[1] if len(args) > 1 else user.first_name

    love_percent = random.randint(0, 100)
    total_blocks = 10

    msg = await update.message.reply_text(f"💖 Совместимость с {target_name}: 0%\n[{'💔'*total_blocks}]")

    current_percent = 0
    while current_percent < love_percent:
        filled_blocks = current_percent * total_blocks // 100
        bar = "💖" * filled_blocks + "💔" * (total_blocks - filled_blocks)
        await msg.edit_text(f"💖 Совместимость с {target_name}: {current_percent}%\n[{bar}]")
        await asyncio.sleep(0.2)
        current_percent += random.randint(1, 5)

    filled_blocks = love_percent * total_blocks // 100
    bar = "💖" * filled_blocks + "💔" * (total_blocks - filled_blocks)
    phrase = random.choice(LOVE_PHRASES)
    if random.random() < 0.2:
        phrase = random.choice(LOVE_JOKES)
    await msg.edit_text(f"💞 Совместимость с {target_name}: {love_percent}%\n[{bar}]\n{phrase}\n{SIGNATURE}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not BOT_ACTIVE:
        return
    message = update.message
    if not message or not message.from_user:
        return
    username = message.from_user.username
    if username in TARGET_USERNAMES and random.random() < 0.3:
        while True:
            phrase = random.choice(LOVE_PHRASES)
            if last_messages.get(username) != phrase:
                last_messages[username] = phrase
                break
        await message.reply_text(f"{phrase}\n\n{SIGNATURE}", reply_to_message_id=message.message_id)

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("love", love_command))
    app.add_handler(CommandHandler("on", turn_on))
    app.add_handler(CommandHandler("off", turn_off))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
