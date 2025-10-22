import os
import threading
import asyncio
import random
import re
from http.server import BaseHTTPRequestHandler, HTTPServer
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes
)

# -----------------------
# 🔑  Конфигурация
# -----------------------
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise RuntimeError("Ошибка: TELEGRAM_TOKEN не установлен!")

OWNER_ID = 8486672898          # <-- замени на свой id, если нужно
LOG_CHANNEL_ID = -1003107269526
bot_active = True

# хранилище
last_messages = {}             # chat_id -> chat_id (для /all)
saved_troll_template = None    # список строк для /troll
troll_stop = False

# тексты для /love и /gift
LOVE_PHRASES = [
    "Ты мне дорог", "Я рад, что ты есть", "Ты особенная", "Ты мой человек",
    "С тобой спокойно", "Ты просто счастье", "Ты делаешь день лучше", "Ты важна",
    "Ты мой уют", "Ты как свет", "Ты делаешь меня лучше", "С тобой всё по-другому",
    "Ты моя радость", "Ты моё вдохновение", "Ты просто прекрасна", "Ты моё всё",
]
SPECIAL_PHRASES = [
    "С тобой даже тишина звучит красиво 💫",
    "Ты — причина чьей-то улыбки 💖",
]
LOVE_JOKES = ["Ты как Wi-Fi — рядом, и всё идеально 😄"]
LOVE_LEVELS = [
    (0, 10, "💔 Лёд между сердцами... но всё ещё есть шанс."),
    (11, 25, "🌧️ Едва заметная искра."),
    (26, 45, "💫 Симпатия растёт."),
    (46, 65, "💞 Нежное притяжение."),
    (66, 80, "💖 Сердца бьются в унисон."),
    (81, 95, "💘 Это почти любовь."),
    (96, 100, "💍 Судьба связала вас — любовь навсегда."),
]
GIFTS_ROMANTIC = ["💐 Букет слов и немного нежности", "🍫 Шоколад из чувства симпатии"]
GIFTS_FUNNY = ["🍕 Один кусочек любви и три крошки заботы", "🍟 Картошка с соусом симпатии"]

# -----------------------
# Мини-вебсервер (Render)
# -----------------------
def run_web():
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"LoveBot is running <3")
    port = int(os.environ.get("PORT", 10000))
    HTTPServer(("0.0.0.0", port), Handler).serve_forever()

threading.Thread(target=run_web, daemon=True).start()

# -----------------------
# Вспомогательные
# -----------------------
async def send_log(context: ContextTypes.DEFAULT_TYPE, text: str):
    # пытаемся отправить лог в канал — если нет прав/канала, просто печатаем
    try:
        if context and context.bot:
            await context.bot.send_message(chat_id=LOG_CHANNEL_ID, text=text)
    except Exception:
        print("LOG:", text)

def split_smart_into_lines(text: str):
    """
    Если в тексте есть реальные переносы - используем их.
    Иначе делим по 30-40 слов (рандомно), чтобы строки выглядели естественно.
    """
    if "\n" in text:
        return [ln.strip() for ln in text.split("\n") if ln.strip()]
    words = text.split()
    lines = []
    i = 0
    # выбираем шаг (30..40) чтобы не ломать слишком часто
    step = random.randint(30, 40)
    while i < len(words):
        lines.append(" ".join(words[i:i+step]))
        i += step
    return lines

# -----------------------
# Команды: включение/выключение
# -----------------------
async def onbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if update.message is None or update.effective_user is None:
        return
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Только владелец.")
        return
    bot_active = True
    await update.message.reply_text("🔔 Бот снова активен!")
    await send_log(context, "Бот включён.")

async def offbot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global bot_active
    if update.message is None or update.effective_user is None:
        return
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("🚫 Только владелец.")
        return
    bot_active = False
    await update.message.reply_text("⚠️ Бот отключён — отвечает только на команды.")
    await send_log(context, "Бот отключён.")

# -----------------------
# /trollsave — сохраняем шаблон
# -----------------------
async def trollsave_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global saved_troll_template
    if update.message is None or update.effective_user is None:
        return
    if update.effective_user.id != OWNER_ID:
        return

    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("❌ Используй: /trollsave <текст> (можно с \\n или реальными переносами).")
        return
    text = parts[1].strip()
    saved_troll_template = split_smart_into_lines(text)
    await update.message.reply_text(f"✅ Шаблон сохранён: {len(saved_troll_template)} строк.")
    # пытаемся удалить команду, игнорируем ошибки
    try:
        await update.message.delete()
    except Exception:
        pass
    await send_log(context, f"/trollsave: сохранено {len(saved_troll_template)} строк.")

# -----------------------
# /troll — лесенка (быстро, построчно)
# -----------------------
async def troll_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global troll_stop, saved_troll_template
    if update.message is None or update.effective_user is None:
        return
    if update.effective_user.id != OWNER_ID:
        return
    if not saved_troll_template:
        await update.message.reply_text("❌ Нет сохранённого шаблона. Используй /trollsave.")
        return

    troll_stop = False
    # удаляем команду (если возможен)
    try:
        await update.message.delete()
    except Exception:
        pass

    chat_id = update.effective_chat.id

    # Быстрая лесенка: отправляем каждую строку отдельным сообщением.
    # Между отправками минимальная пауза 0.01 сек (очень быстро).
    # Если в группе/канале Telegram режет скорость, можно увеличить паузу.
    for line in saved_troll_template:
        if troll_stop:
            break
        try:
            await context.bot.send_message(chat_id=chat_id, text=line)
        except Exception as e:
            # при ошибке — логируем и продолжаем
            print("Ошибка отправки строки в /troll:", e)
            await send_log(context, f"Ошибка отправки строки в /troll: {e}")
        # минимальная задержка
        await asyncio.sleep(0.01)

    # после завершения
    if not troll_stop:
        try:
            await context.bot.send_message(chat_id=chat_id, text="✅ Троллинг завершён! 💞")
        except Exception:
            pass
    await send_log(context, "/troll завершён или остановлен.")

# -----------------------
# /trollstop
# -----------------------
async def trollstop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global troll_stop
    if update.message is None or update.effective_user is None:
        return
    if update.effective_user.id != OWNER_ID:
        return
    troll_stop = True
    try:
        await update.message.reply_text("🛑 Троллинг остановлен!")
    except Exception:
        pass
    await send_log(context, "/trollstop вызван.")

# -----------------------
# /all — рассылка
# -----------------------
async def all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None or update.effective_user is None:
        return
    if update.effective_user.id != OWNER_ID:
        return
    text = re.sub(r'^/all\s+', '', update.message.text, flags=re.I).strip()
    if not text:
        await update.message.reply_text("❌ Введи текст: /all <текст>")
        return
    count = 0
    for chat_id in list(last_messages.keys()):
        try:
            await context.bot.send_message(chat_id=chat_id, text=text)
            count += 1
            # небольшая пауза чтобы не резать API
            await asyncio.sleep(0.02)
        except Exception:
            continue
    await update.message.reply_text(f"✅ Рассылка завершена, отправлено в ~{count} чатов.")
    await send_log(context, f"/all: отправлено в {count} чатов.")

# -----------------------
# /love — проверка совместимости
# -----------------------
async def love_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    # бот отвечает только если активен
    if not bot_active:
        return
    try:
        args = update.message.text.split(maxsplit=1)
        initiator = update.effective_user.username or update.effective_user.first_name
        target = args[1].replace("@", "") if len(args) > 1 else initiator
        score = random.randint(0, 100)
        # бар
        bar_len = 20
        filled = score * bar_len // 100
        hearts = "❤️" * (filled // 2)  # просто визуалка
        bars = hearts + "🖤" * (bar_len - len(hearts))
        sent = await update.message.reply_text(f"💞 @{initiator} 💖 @{target}\n{score}% [{bars}]")
        # "анимация"
        for _ in range(2):
            await asyncio.sleep(0.15)
            try:
                await sent.edit_text(f"💞 @{initiator} 💖 @{target}\n{score}% [{bars}]")
            except Exception:
                pass
        phrase = random.choice(SPECIAL_PHRASES if target.lower() == SIGNATURE_USER.lower() if ( 'SIGNATURE_USER' in globals() ) else False else LOVE_PHRASES + LOVE_JOKES)
        category = next((lbl for (lo, hi, lbl) in LOVE_LEVELS if lo <= score <= hi), "💞 Нежные чувства")
        res = f"💞 @{initiator} 💖 @{target}\n🎯 Результат: {score}% [{bars}]\n{phrase}\n\nКатегория: {category}"
        # подпись для особого пользователя (если определён)
        try:
            if 'SIGNATURE_TEXT' in globals() and 'SIGNATURE_USER' in globals() and target.lower() == SIGNATURE_USER.lower():
                res += f"\n\n{SIGNATURE_TEXT}"
        except Exception:
            pass
        await sent.edit_text(res)
        await send_log(context, f"/love: @{initiator} -> @{target} = {score}%")
    except Exception as e:
        print("Ошибка /love:", e)
        await send_log(context, f"Ошибка /love: {e}")

# -----------------------
# /gift — подарок
# -----------------------
async def gift_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    if not bot_active:
        return
    args = update.message.text.split(maxsplit=1)
    if len(args) < 2:
        await update.message.reply_text("🎁 Используй: /gift @username")
        return
    giver = update.effective_user.username or update.effective_user.first_name
    target = args[1].replace("@", "")
    gift = random.choice(GIFTS_ROMANTIC if random.choice([True, False]) else GIFTS_FUNNY)
    msg = await update.message.reply_text(f"🎁 @{giver} дарит @{target} подарок:\n🎁 …")
    # мини-анимация
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
# Логирование чатов (для /all) и автоответные правила
# -----------------------
async def handle_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # защитимся от пустых апдейтов
    if update.message is None:
        return
    # сохраняем chat_id
    try:
        last_messages[update.message.chat.id] = update.message.chat.id
    except Exception:
        pass
    # если бот выключен — отвечаем только на команды (т.е. здесь не отвечаем)
    if not bot_active:
        return

# -----------------------
# Регистрация и запуск
# -----------------------
if __name__ == "__main__":
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    # регистрируем команды
    app.add_handler(CommandHandler("onbot", onbot))
    app.add_handler(CommandHandler("offbot", offbot))
    app.add_handler(CommandHandler("trollsave", trollsave_cmd))
    app.add_handler(CommandHandler("troll", troll_cmd))
    app.add_handler(CommandHandler("trollstop", trollstop_cmd))
    app.add_handler(CommandHandler("all", all_cmd))
    app.add_handler(CommandHandler("love", love_cmd))
    app.add_handler(CommandHandler("gift", gift_cmd))

    # логирование всех текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_messages))

    print("✅ Love+Troll Bot запущен!")
    app.run_polling()
