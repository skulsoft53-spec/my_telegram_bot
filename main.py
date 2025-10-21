import os
import random
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    MessageHandler,
    CommandHandler,
    filters,
    ContextTypes
)

# Проверка токена
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Ошибка: переменная окружения TELEGRAM_TOKEN не установлена!")
print("✅ TELEGRAM_TOKEN найден, бот запускается...")

# Пользователи, на которых бот отвечает
TARGET_USERNAMES = ["Habib471"]
SIGNATURE = "Полюби Апачи, как он тебя"

# 100 красивых романтических фраз
LOVE_PHRASES = [
    "Ты — моё вдохновение, нежное как дыхание весны",
    "С тобой каждый день становится чудом",
    "Ты — моя мелодия счастья",
    "В твоих глазах я вижу небо и свет",
    "Каждое твое слово — как ветерок, что успокаивает",
    "С тобой даже тишина звучит прекраснее",
    "Ты — дыхание света в моём сердце",
    "Когда ты рядом, мир кажется мягче и ярче",
    "Ты — утренний луч, что пробивает мрак",
    "С тобой каждый момент — страница красивой книги",
    "Ты — капля любви в океане жизни",
    "В твоей улыбке спрятан целый мир",
    "Ты — мой якорь и мой полёт одновременно",
    "Каждое утро с тобой — праздник души",
    "Ты — мягкий свет, что ведёт меня сквозь тьму",
    "С тобой каждая минута превращается в волшебство",
    "Ты — смысл, делающий всё второстепенным",
    "С тобой даже дождь кажется музыкой",
    "Ты — мой внутренний покой и буря одновременно",
    "Ты — моя бесконечность в одном взгляде",
    "Ты — утренний рассвет, озаряющий мою жизнь",
    "С тобой даже серые дни становятся яркими",
    "Ты — песня, которую хочется слушать бесконечно",
    "Каждое прикосновение твоей руки — шёпот счастья",
    "Ты — мой маяк в буре жизни",
    "С тобой хочется создавать чудеса каждый день",
    "Ты — аромат весны в моих мыслях",
    "Когда ты смеёшься, мир кажется идеальным",
    "Ты — мягкий свет среди сумрака",
    "С тобой я чувствую себя целым",
    "Ты — моя любимая случайность",
    "Каждое твое слово — строчка красивой поэмы",
    "Ты — моё вдохновение даже в сомнениях",
    "С тобой хочется лететь",
    "Ты — тихая радость, согревающая сердце",
    "Когда ты рядом, мир дышит в унисон",
    "Ты — мягкий шёпот счастья",
    "С тобой я учусь видеть красоту в каждом мгновении",
    "Ты — нежность, превращающая обыденность в чудо",
    "Каждое утро с тобой — как первый вдох",
    "Ты — лучик света, что рассекает мрак",
    "С тобой жизнь обретает ритм мелодии",
    "Ты — моя тихая гавань",
    "Каждое твое движение — танец вселенной",
    "Ты — вдохновение, превращающее мысли в поэзию",
    "С тобой даже молчание звучит как музыка",
    "Ты — мой космос, полный светлых звёзд",
    "Когда ты рядом, время замирает",
    "Ты — тёплое облако в холодном мире",
    "С тобой даже простые слова обретают смысл",
    "Ты — мой утренний кофе",
    "Каждое твое «привет» — солнечный луч",
    "Ты — тихая музыка, что звучит только для меня",
    "С тобой хочется мечтать и верить",
    "Ты — лёгкость, растворяющая тяжесть забот",
    "Каждое твое дыхание — новая жизнь для души",
    "Ты — мягкий свет, что никогда не погаснет",
    "С тобой мир становится ярче и настоящим",
    "Ты — причудливый узор счастья",
    "Когда ты смотришь на меня, я вижу вселенную",
    "Ты — мой уют в холодные дни",
    "С тобой каждый день — волшебная сказка",
    "Ты — любимая глава в книге жизни",
    "Каждое твое слово — ласковое прикосновение",
    "Ты — свет, превращающий тьму в рассвет",
    "С тобой ощущаю гармонию",
    "Ты — вечная весна, расцветающая в сердце",
    "Каждое мгновение с тобой — драгоценность",
    "Ты — тихая радость среди шумного мира",
    "С тобой даже дождь — симфония",
    "Ты — мой компас в жизни",
    "Когда ты рядом, хочется улыбаться",
    "Ты — мягкий шелест листвы в сердце",
    "С тобой хочу идти по жизни навсегда",
    "Ты — вдохновляющая тишина",
    "Каждое прикосновение — сияние солнца",
    "Ты — мягкий шёпот, что лечит страхи",
    "С тобой хочется творить, мечтать и жить",
    "Ты — смысл, делающий жизнь настоящей",
    "Когда ты смеёшься, мир добрее",
    "Ты — тихая гавань и буря одновременно",
    "С тобой каждый день — красивая история",
    "Ты — мягкое прикосновение света к душе",
    "Каждое слово — мелодия счастья",
    "Ты — утренний рассвет и вечерняя звезда",
    "С тобой хочется быть лучше",
    "Ты — бесконечная мечта, ставшая явью",
    "Когда ты рядом, всё возможно",
    "Ты — нежность, делающая мир мягче",
    "С тобой хочется останавливаться в каждом моменте",
    "Ты — маленькое чудо каждый день",
    "Каждое мгновение — дыхание радости",
    "Ты — музыка, звучащая без слов",
    "С тобой обычный день — волшебный",
    "Ты — мягкий свет, остающийся в душе",
    "Ты — вдохновляющая сказка, которую хочется перечитывать",
]

# Мини-шутки
LOVE_JOKES = [
    "Ты как Wi-Fi — когда рядом, всё идеально 😄",
    "Ты — моя батарейка, без тебя я теряю заряд ❤️",
    "Если бы ты был кофе, я бы никогда не просыпался ☕",
    "Ты как пароль: сложный, но без тебя жизнь невозможна 🔑",
    "Ты — песня, которую хочу слушать на повторе 🎶",
    "С тобой даже понедельник весёлый 😆",
]

# Веб-сервер для Render/Heroku
def run_web():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"LoveBot is running <3")
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()

# Последнее сообщение
last_messages = {}
bot_active = True  # флаг работы бота

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💞 Привет! Я LoveBot by Apachi.\n"
        "Я отвечаю на сообщения выбранных пользователей 💌\n"
        "Командой /love можно проверить совместимость!"
    )

async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bot_active:
        return
    message = update.message
    args = message.text.split(maxsplit=1)
    target = args[1] if len(args) > 1 else message.from_user.username
    score = random.randint(0, 100)
    await message.reply_text(f"💞 Совместимость с {target}: {score}%")

async def turn_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    bot_active = True
    await update.message.reply_text("✅ Бот включен и готов отвечать 💌")

async def turn_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    bot_active = False
    await update.message.reply_text("❌ Бот отключен. Он больше не будет отвечать.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bot_active:
        return
    message = update.message
    if not message or not message.from_user:
        return
    username = message.from_user.username
    if message.chat.type in ["group", "supergroup"]:
        if username in TARGET_USERNAMES and random.random() < 0.3:
            phrase = None
            # 20% шанс на шутку
            if random.random() < 0.2:
                while True:
                    phrase = random.choice(LOVE_JOKES)
                    if last_messages.get(username) != phrase:
                        last_messages[username] = phrase
                        break
            else:
                while True:
                    phrase = random.choice(LOVE_PHRASES)
                    if last_messages.get(username) != phrase:
                        last_messages[username] = phrase
                        break
            response = phrase + f"\n\n{SIGNATURE}"
            await message.reply_text(response, reply_to_message_id=message.message_id)

# Запуск бота
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("love", love_command))
    app.add_handler(CommandHandler("on", turn_on))
    app.add_handler(CommandHandler("off", turn_off))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("🚀 Бот запущен и работает...")
    app.run_polling()
