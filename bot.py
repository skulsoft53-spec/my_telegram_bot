import os
import re
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.filters import Command
from spellchecker import SpellChecker

# ===== НАСТРОЙКИ =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Не указан BOT_TOKEN")

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_SECRET = "supersecret"
WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL")
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

PORT = int(os.getenv("PORT", 10000))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
spell = SpellChecker(language="ru")

existing_biographies_texts = []  # сюда можно добавить сохранённые биографии


# ===== Команда /start =====
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "📄 Отправьте RP биографию одним сообщением.\n\n"
        "Заголовок: Биография | Nick_Name\n"
        "В конце: Font=Times New Roman|Size=15\n"
        "Фото обязательно прикрепить."
    )


# ===== Проверка биографии =====
@dp.message()
async def check_bio(message: types.Message):
    if not message.text:
        await message.answer("❌ Биография должна быть отправлена текстом.")
        return

    text = message.text
    lines = text.split("\n")
    reasons_minor = []  # на доработку
    reasons_major = []  # отклонение

    words = re.findall(r"\w+", text, flags=re.UNICODE)
    word_count = len(words)

    # ===== Критические ошибки =====
    fantasy_words = ["маг","бессмерт","телепорт","суперсил","невидим","вампир","демон"]
    if any(word in text.lower() for word in fantasy_words):
        reasons_major.append("Обнаружены сверхспособности (нереалистичный персонаж).")

    real_people = ["брэд питт","аль капоне","elon musk"]
    if any(name in text.lower() for name in real_people):
        reasons_major.append("Запрещено писать биографию существующей личности.")

    forbidden = ["убиваю всех","маньяк","террорист","насильник","психически больной"]
    if any(word in text.lower() for word in forbidden):
        reasons_major.append("Биография содержит запрещённые элементы.")

    # ===== Мелкие ошибки =====
    title = lines[0].strip()
    if not re.match(r"^Биография \| [A-Za-zА-Яа-я0-9_]+$", title):
        reasons_minor.append("Неверный формат заголовка.")

    if word_count < 200:
        reasons_minor.append(f"Недостаточный объём ({word_count} слов). Минимум 200.")
    elif word_count > 600:
        reasons_minor.append(f"Превышен объём ({word_count} слов). Максимум 600.")

    if not message.photo:
        reasons_minor.append("Отсутствуют прикреплённые фотографии.")

    font_match = re.search(r"Font=([\w\s]+)\|Size=(\d+)", text)
    if font_match:
        font = font_match.group(1).strip().lower()
        size = int(font_match.group(2))
        if font not in ["times new roman","verdana"]:
            reasons_minor.append("Разрешён только Times New Roman или Verdana.")
        if size < 15:
            reasons_minor.append("Размер шрифта должен быть не менее 15.")
    else:
        reasons_minor.append("Не указан шрифт и размер в формате Font=...|Size=...")

    filtered_words = [w.lower() for w in words if len(w) > 2 and not re.search(r"\d", w)]
    misspelled = spell.unknown(filtered_words)
    if len(misspelled) > 5:
        reasons_minor.append(f"Слишком много орфографических ошибок (пример: {', '.join(list(misspelled)[:5])}).")

    age_match = re.search(r"Возраст:\s*(\d+)", text)
    if age_match:
        age = int(age_match.group(1))
        if age < 18 and "университет" in text.lower():
            reasons_minor.append("Возраст не соответствует обучению в университете.")
        if age < 21 and "бизнес" in text.lower():
            reasons_minor.append("Возраст не соответствует ведению бизнеса.")
    else:
        reasons_minor.append("Не указан возраст персонажа.")

    required_sections = [
        "Имя и фамилия персонажа:",
        "Пол:",
        "Возраст:",
        "Национальность:",
        "Образование:",
        "Описание внешности:",
        "Характер:",
        "Детство:",
        "Настоящее время:",
        "Итог:"
    ]
    for section in required_sections:
        if section.lower() not in text.lower():
            reasons_minor.append(f"Отсутствует раздел: {section}")

    # ===== Итог =====
    if reasons_major:
        msg = "❌ Биография отклонена (критические ошибки):\n\n"
        for r in reasons_major:
            msg += f"• {r}\n"
        msg += "\nИсправить невозможно — отправьте новую биографию."
    elif reasons_minor:
        msg = "⚠️ Биография на доработке:\n\n"
        for r in reasons_minor:
            msg += f"• {r}\n"
        msg += "\n⏳ У вас есть 24 часа на исправление и повторную отправку."
    else:
        msg = "✅ Биография одобрена.\n\nВаша RP биография соответствует правилам."

    await message.answer(msg)


# ===== WEBHOOK =====
async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL, secret_token=WEBHOOK_SECRET)
    logging.info(f"Webhook установлен: {WEBHOOK_URL}")


async def on_shutdown(app):
    await bot.delete_webhook()


def main():
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=WEBHOOK_SECRET,
    ).register(app, path=WEBHOOK_PATH)

    setup_application(app, dp, bot=bot)

    web.run_app(app, host="0.0.0.0", port=PORT)


if __name__ == "__main__":
    main()
