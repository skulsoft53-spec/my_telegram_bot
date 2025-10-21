import os
import threading
import time
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, MessageHandler, CommandHandler,
    filters, ContextTypes
)
import random

# 🔑 Токен
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Ошибка: переменная окружения TELEGRAM_TOKEN не установлена!")
print("✅ TELEGRAM_TOKEN найден, бот запускается...")

# ⚙️ Настройки
TARGET_USERNAMES = ["Habib471"]
SIGNATURE_USER = "Habib471"
SIGNATURE_TEXT = "Полюби Апачи, как он тебя 💞"
OWNER_USERNAME = "bxuwy"  # Только ты можешь использовать команды управления

bot_active = True
last_messages = {}
muted_users = {}  # username: unmute_timestamp (или None, если навсегда)

# 💖 Простые романтические фразы (без эмодзи, 70+)
LOVE_PHRASES = [
    "Ты мне дорог", "Я рад, что ты есть", "Ты особенная", "Ты мой человек", "С тобой спокойно",
    "Ты просто счастье", "Ты делаешь день лучше", "Ты важна", "Ты мой уют", "Ты как свет",
    "Ты делаешь меня лучше", "С тобой всё по-другому", "Ты моя радость", "Ты мой светлый человек",
    "Ты моё вдохновение", "Ты просто прекрасна", "Ты мой свет в любой день",
    "Ты человек, которого не заменить", "Ты моё всё", "Ты дыхание моих чувств",
    "Ты часть моего мира", "Ты нежность моего сердца", "Ты моё утро и мой покой",
    "Ты чудо, подаренное судьбой", "Ты наполняешь жизнь смыслом", "Ты мой покой в шумном мире",
    "С тобой хочется жить", "Ты делаешь меня счастливым", "Ты — моё настоящее",
    "Ты — лучшее, что со мной случалось", "Ты как солнце после дождя",
    "Ты даришь тепло даже молчанием", "Ты — моя гармония", "Ты — мой дом",
    "Ты всегда в моих мыслях", "Ты — причина моего вдохновения", "Ты приносишь свет туда, где темно",
    "Ты — мой самый нежный человек", "Ты даёшь мне силы", "Ты — мой уют и покой",
    "С тобой всё имеет смысл", "Ты наполняешь меня радостью", "Ты — мой смысл",
    "Ты — человек, которого хочется беречь", "Ты — счастье, о котором я не просил, но получил",
    "Ты — мой тихий рай", "Ты — мой день и моя ночь", "Ты — нежность, в которой хочется остаться",
    "Ты — самая добрая часть моего сердца", "Ты делаешь жизнь ярче",
    "Ты — человек, с которым хочется всё", "Ты — мой вдохновитель",
    "Ты — человек, ради которого стоит жить", "Ты — мой внутренний свет",
    "Ты — моё спокойствие в этом мире", "Ты — мечта, ставшая реальностью",
    "Ты — самое тёплое чувство во мне", "Ты — человек, которому можно доверить сердце",
    "Ты — мой нежный шторм", "Ты — человек, рядом с которым всё становится возможным",
    "Ты — мой самый ценный человек", "Ты — причина моего счастья",
    "Ты — человек, с которым время останавливается", "Ты — мой нежный свет",
    "Ты — человек, которого я не хочу терять", "Ты — дыхание моей души",
    "Ты — человек, который делает мир красивее", "Ты — моё вдохновение и покой одновременно",
    "Ты — нежность, которой не хватает этому миру", "Ты — человек, без которого день неполный",
    "Ты — моя самая добрая мысль"
]

SPECIAL_PHRASES = [
    "С тобой даже тишина звучит красиво 💫",
    "Ты — причина улыбки Апачи 💖",
    "Когда ты рядом, весь мир добрее 🌸",
    "Ты — вдохновение Апачи 💞",
    "Ты — свет, в котором он живёт ☀️",
    "Ты — чувство, которое невозможно описать словами 💓",
    "Апачи просто видит в тебе особенное 🌹",
    "Ты — тот человек, ради которого хочется быть лучше 💫",
    "Ты — искренность, которую он ценит 💖",
    "Полюби Апачи, как он тебя 💞"
]

LOVE_JOKES = [
    "Ты как Wi-Fi — рядом, и всё идеально 😄",
    "Ты — батарейка, без тебя теряю заряд 🔋",
    "Если бы ты был кофе, не просыпался бы без тебя ☕",
    "Ты как пароль: сложный, но жизнь без тебя невозможна 🔑",
    "Ты — любимая песня на повторе 🎶",
]

LOVE_LEVELS = [
    (0, 10, "💔 Лёд между сердцами... но всё ещё есть шанс."),
    (11, 25, "🌧️ Едва заметная искра, но она может вспыхнуть."),
    (26, 45, "💫 Симпатия растёт, пусть время покажет."),
    (46, 65, "💞 Нежное притяжение между вами."),
    (66, 80, "💖 Сердца начинают биться в унисон."),
    (81, 95, "💘 Это почти любовь — искренняя и сильная."),
    (96, 100, "💍 Судьба связала вас — любовь навсегда."),
]

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

# ⏱ Вспомогательная функция
def parse_duration(duration_str):
    match = re.match(r"(\d+)([smhd])", duration_str)
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2)
    return {"s": value, "m": value * 60, "h": value * 3600, "d": value * 86400}[unit]

# 💬 Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💞 Привет! Я LoveBot by Apachi.\n"
        "Команда /love покажет процент любви 💌\n"
        "Команды /мут и /мутстоп доступны только создателю бота."
    )

async def mute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.username != OWNER_USERNAME:
        return await update.message.reply_text("🚫 Только создатель может использовать эту команду.")
    if len(context.args) == 0:
        return await update.message.reply_text("⚠️ Используй: /мут @username [время, напр. 10m]")

    username = context.args[0].replace("@", "")
    duration = None
    if len(context.args) > 1:
        duration = parse_duration(context.args[1])

    unmute_time = time.time() + duration if duration else None
    muted_users[username] = unmute_time

    msg = f"🔇 Пользователь @{username} получил мут"
    if duration:
        msg += f" на {context.args[1]}"
    else:
        msg += " навсегда"
    await update.message.reply_text(msg)

async def unmute_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.username != OWNER_USERNAME:
        return await update.message.reply_text("🚫 Только создатель может использовать эту команду.")
    if len(context.args) == 0:
        return await update.message.reply_text("⚠️ Используй: /мутстоп @username")

    username = context.args[0].replace("@", "")
    if username in muted_users:
        del muted_users[username]
        await update.message.reply_text(f"🔊 @{username} теперь может писать снова.")
    else:
        await update.message.reply_text(f"ℹ️ @{username} не был в муте.")

# 💘 Команда /love
async def love_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bot_active:
        return
    message = update.message
    args = message.text.split(maxsplit=1)
    target = args[1].replace("@", "") if len(args) > 1 else message.from_user.username

    score = random.randint(0, 100)
    phrase = random.choice(SPECIAL_PHRASES if target.lower() == SIGNATURE_USER.lower() else LOVE_PHRASES + LOVE_JOKES)
    category = next((label for (low, high, label) in LOVE_LEVELS if low <= score <= high), "💞 Нежные чувства")
    emojis = "".join(random.choices(["💖", "✨", "🌹", "💫", "💓", "🌸", "⭐"], k=4))

    text_to_send = (
        f"💞 Проверяем совместимость между @{message.from_user.username} и @{target}...\n"
        f"🎯 Результат: {score}%\n\n{phrase}\n\nКатегория: {category} {emojis}"
    )
    if target.lower() == SIGNATURE_USER.lower():
        text_to_send += f"\n\n{SIGNATURE_TEXT}"
    await message.reply_text(text_to_send)

# 💬 Обработка сообщений
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.from_user:
        return
    username = message.from_user.username
    if not username:
        return

    # Проверяем мут
    if username in muted_users:
        if muted_users[username] and time.time() > muted_users[username]:
            del muted_users[username]
        else:
            try:
                await message.delete()
            except:
                pass
            return

    # Реакция на выбранных пользователей
    if message.chat.type in ["group", "supergroup"] and username in TARGET_USERNAMES:
        phrase = random.choice(SPECIAL_PHRASES)
        while last_messages.get(username) == phrase:
            phrase = random.choice(SPECIAL_PHRASES)
        last_messages[username] = phrase
        await message.reply_text(f"{phrase}\n\n{SIGNATURE_TEXT}", reply_to_message_id=message.message_id)

# 🚀 Запуск
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("love", love_command))
    app.add_handler(CommandHandler("мут", mute_command))
    app.add_handler(CommandHandler("мутстоп", unmute_command))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

    print("💘 LoveBot запущен с командой МУТ!")
    app.run_polling()

if __name__ == "__main__":
    main()
