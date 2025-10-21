import os
import random
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# Пользователи, на которых бот отвечает
TARGET_USERNAMES = ["Habib471"]
SIGNATURE = "Полюби Апачи, как он тебя"

# 100 красивых романтических фраз
LOVE_PHRASES = [
    "Ты — моё вдохновение и свет в сердце",
    "С тобой каждый день становится чудом",
    "Ты — моя мелодия счастья и тепла",
    "В твоих глазах я вижу бесконечность",
    "Каждое твоё слово — как ласковый шёпот",
    "Ты — утренний лучик света в моей жизни",
    "С тобой даже тишина наполняется смыслом",
    "Ты — дыхание весны в моём сердце",
    "Когда ты рядом, мир кажется мягче",
    "Ты — капля радости в моём дне",
    "С тобой хочу делить каждый момент",
    "Ты — смысл моих самых светлых мыслей",
    "Твоя улыбка согревает мою душу",
    "Ты — моя тихая гавань среди бури",
    "С тобой хочется мечтать без конца",
    "Ты — мягкий свет, что ведёт меня",
    "Каждое прикосновение твоей руки — счастье",
    "Ты — музыка, что звучит без слов",
    "С тобой даже дождь кажется красивым",
    "Ты — мой маяк в буре жизни",
    "Когда ты смеёшься, мир улыбается",
    "Ты — аромат весны в моих мыслях",
    "С тобой каждый день как маленькое чудо",
    "Ты — моя любимая случайность",
    "Каждое утро с тобой — праздник души",
    "Ты — мягкий свет среди сумрака",
    "С тобой хочу лететь, даже не касаясь земли",
    "Ты — тихая радость, что согревает сердце",
    "Когда ты рядом, сердце бьётся быстрее",
    "Ты — мягкий шёпот счастья в тишине",
    "С тобой мир наполняется гармонией",
    "Ты — моя бесконечность в одном взгляде",
    "Каждое мгновение с тобой — драгоценность",
    "Ты — тепло, что остаётся в душе",
    "С тобой хочется творить и мечтать",
    "Ты — утренний рассвет и вечерняя звезда",
    "Каждое твоё слово — как прикосновение света",
    "Ты — мягкий шелест листвы в сердце",
    "С тобой жизнь обретает новые цвета",
    "Ты — моя гармония среди хаоса",
    "С тобой хочется останавливаться в каждом мгновении",
    "Ты — смысл, который делает всё настоящим",
    "Каждое твоё «привет» — как солнечный луч",
    "Ты — вдохновение, что оживляет мысли",
    "С тобой даже обычный день становится волшебством",
    "Ты — моя тихая музыка, что звучит только для меня",
    "С тобой хочется идти по жизни, держась за руку",
    "Ты — мой космос, полный светлых звёзд",
    "Каждое твоё движение — как танец вселенной",
    "Ты — мягкое прикосновение света к душе",
    "С тобой хочется любить и верить в чудеса",
    "Ты — моя вечная весна, что расцветает в сердце",
    "Каждое мгновение с тобой — как дыхание радости",
    "Ты — свет, который превращает тьму в рассвет",
    "С тобой хочется быть лучше и видеть лучшее",
    "Ты — моя вдохновляющая сказка, которую хочется перечитывать",
    "Ты — теплое облако в холодном мире",
    "С тобой каждый день похож на волшебную сказку",
    "Ты — моя любимая глава в книге моей жизни",
    "Каждое твоё слово — как ласковое прикосновение",
    "Ты — мой компас, что ведёт к счастью",
    "Когда ты смотришь на меня, я вижу всё ценное",
    "Ты — моя тихая гавань и буря одновременно",
    "С тобой каждый день превращается в историю",
    "Ты — лучик света, который не гаснет в сердце",
    "С тобой хочется творить без конца",
    "Ты — вдохновение, что превращает мысли в поэзию",
    "Каждое твоё прикосновение — как сияние солнца",
    "Ты — мягкий шёпот, что лечит сомнения и страхи",
    "С тобой хочется жить полной жизнью",
    "Ты — смысл, который делает мою жизнь настоящей",
    "Когда ты смеёшься, мир кажется добрее",
    "Ты — мягкое прикосновение счастья",
    "С тобой ощущаю вечность в каждом мгновении",
    "Ты — утренний кофе, без которого не начинается день",
    "Каждое твоё «спокойной ночи» — как объятие",
    "Ты — музыка, что звучит в сердце",
    "С тобой хочется верить, что чудеса существуют",
    "Ты — лёгкость, что растворяет тяжесть забот",
    "Каждое твоё дыхание — новая жизнь для души",
    "Ты — мягкий свет в сердце, что никогда не погаснет",
    "С тобой мир становится ярче и настоящим",
    "Ты — причудливый узор счастья в моих днях",
    "Когда ты смотришь на меня, я вижу вселенную",
    "Ты — мой уют даже в пасмурные дни",
    "С тобой хочу создавать маленькие чудеса",
    "Ты — вдохновение, что оживляет каждую мысль",
    "Каждое твоё слово — как строчка красивой поэмы",
    "Ты — мягкий свет, что ведёт сквозь тьму",
    "С тобой хочется мечтать и верить в любовь",
    "Ты — моя тихая радость среди шумного мира",
    "С тобой даже дождь становится симфонией",
    "Ты — компас моей души, что ведёт к счастью",
    "Когда ты рядом, хочется улыбаться без причины",
    "Ты — вдохновение каждого моего дня",
    "С тобой я ощущаю гармонию, которой не хватает в мире",
    "Ты — мягкий шёпот счастья, который слышу всегда",
    "С тобой хочется идти вперёд, держась за руки",
    "Ты — моя бесконечная мечта, что стала явью",
    "Когда ты рядом, кажется, что всё возможно",
]

# Маленькие шутки
LOVE_JOKES = [
    "Ты как Wi-Fi — когда рядом, всё идеально 😄",
    "Ты — моя батарейка, без тебя теряю заряд ❤️",
    "Если бы ты был кофе, я бы не просыпался без тебя ☕",
    "Ты как пароль: сложный, но без тебя жизнь невозможна 🔑",
    "Ты — любимая песня, которую хочу слушать снова 🎶",
]

# Флаг активности бота
BOT_ACTIVE = True

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

# Последние сообщения, чтобы не повторять
last_messages = {}

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💞 Привет! Я LoveBot by Apachi.\n"
        "Я отвечаю на сообщения выбранных пользователей 💌\n"
        "Командой /love можно проверить совместимость!"
    )

# /love команда
async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not BOT_ACTIVE:
        await update.message.reply_text("Бот сейчас отключен ⚡")
        return

    message = update.message
    args = message.text.split(maxsplit=1)
    target = args[1] if len(args) > 1 else message.from_user.username
    score = random.randint(0, 100)

    if score > 80:
        phrase = "💖 Ваши сердца бьются в унисон!"
    elif score > 50:
        phrase = "💞 Между вами искрится тепло и нежность."
    elif score > 20:
        phrase = "💌 Есть потенциал, не теряйте шанс!"
    else:
        phrase = "😅 Может, стоит дать друг другу время?"

    if random.random() < 0.2:
        phrase += "\n" + random.choice(LOVE_JOKES)

    await message.reply_text(f"💞 Совместимость с {target}: {score}%\n{phrase}")

# Включение/выключение бота
async def turn_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_ACTIVE
    BOT_ACTIVE = True
    await update.message.reply_text("Бот включен ✅")

async def turn_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global BOT_ACTIVE
    BOT_ACTIVE = False
    await update.message.reply_text("Бот отключен ❌")

# Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not BOT_ACTIVE:
        return
    message = update.message
    if not message or not message.from_user:
        return
    username = message.from_user.username
    if username in TARGET_USERNAMES and random.random() < 0.3:
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
async def main():
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        print("Ошибка: установите TELEGRAM_TOKEN")
        return
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("love", love_command))
    app.add_handler(CommandHandler("on", turn_on))
    app.add_handler(CommandHandler("off", turn_off))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    print("Бот запущен!")
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
