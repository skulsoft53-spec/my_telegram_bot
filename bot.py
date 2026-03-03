import logging
import os
import re
from aiogram import Bot, Dispatcher, types
from aiogram.utils.executor import start_webhook
from spellchecker import SpellChecker

# ====== НАСТРОЙКИ ======
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("Не указан BOT_TOKEN")

WEBHOOK_HOST = os.getenv("RENDER_EXTERNAL_URL")
WEBHOOK_PATH = f"/webhook/{API_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = "0.0.0.0"
WEBAPP_PORT = int(os.getenv("PORT", 10000))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
spell = SpellChecker(language="ru")

existing_biographies_texts = []  # сюда можно добавить базу биографий


# ====== СТАРТ ======
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "📄 Отправьте RP биографию одним сообщением.\n\n"
        "Заголовок: Биография | Nick_Name\n"
        "В конце: Font=Times New Roman|Size=15\n"
        "Фото обязательно прикрепить."
    )


# ====== ПРОВЕРКА ======
@dp.message_handler(content_types=types.ContentTypes.ANY)
async def check_bio(message: types.Message):

    if not message.text:
        await message.answer("❌ Биография должна быть отправлена текстом.")
        return

    text = message.text
    lines = text.split("\n")
    reasons = []

    words = re.findall(r"\w+", text, flags=re.UNICODE)
    word_count = len(words)

    # 1.1 Заголовок
    title = lines[0].strip()
    if not re.match(r"^Биография \| [A-Za-zА-Яа-я0-9_]+$", title):
        reasons.append("1.1 Неверный формат заголовка.")

    # 1.9 Объём
    if word_count < 200:
        reasons.append(f"1.9 Недостаточный объём ({word_count} слов, минимум 200).")
    if word_count > 600:
        reasons.append(f"1.9 Превышен объём ({word_count} слов, максимум 600).")

    # 1.5 Орфография
    filtered_words = [w.lower() for w in words if len(w) > 2 and not re.search(r"\d", w)]
    misspelled = spell.unknown(filtered_words)
    if len(misspelled) > 5:
        reasons.append("1.5 Слишком много орфографических ошибок.")

    # 1.6 Шрифт
    font_match = re.search(r"Font=([\w\s]+)\|Size=(\d+)", text)
    if font_match:
        font = font_match.group(1).strip().lower()
        size = int(font_match.group(2))
        if font not in ["times new roman", "verdana"] or size < 15:
            reasons.append("1.6 Неверный шрифт или размер (минимум 15).")
    else:
        reasons.append("1.6 Не указан шрифт и размер.")

    # 1.7 Фото
    if not message.photo:
        reasons.append("1.7 Отсутствуют прикреплённые фотографии.")

    # 1.2 Сверхспособности
    fantasy_words = [
        "маг", "бессмерт", "телепорт", "суперсил",
        "невидим", "вампир", "оборотень", "демон", "сверхспособ"
    ]
    if any(word in text.lower() for word in fantasy_words):
        reasons.append("1.2 Обнаружены сверхспособности (нереалистичный персонаж).")

    # 1.3 Реальные личности
    real_people = [
        "брэд питт", "аль капоне", "elon musk",
        "владимир путин", "джефф безос"
    ]
    if any(name in text.lower() for name in real_people):
        reasons.append("1.3 Биография существующей личности запрещена.")

    # 1.8 Нарушение правил сервера
    forbidden_behavior = [
        "убиваю всех", "маньяк", "террорист",
        "насильник", "психически больной"
    ]
    if any(word in text.lower() for word in forbidden_behavior):
        reasons.append("1.8 Биография содержит запрещённые факторы.")

    # 1.10 Логические противоречия (возраст)
    age_match = re.search(r"Возраст:\s*(\d+)", text)
    if age_match:
        age = int(age_match.group(1))
        if age < 18 and "университет" in text.lower():
            reasons.append("1.10 Возраст не соответствует обучению в университете.")
        if age < 21 and "бизнес" in text.lower():
            reasons.append("1.10 Возраст не соответствует ведению бизнеса.")
    else:
        reasons.append("Не указан возраст.")

    # 1.4 Проверка копирования
    for existing in existing_biographies_texts:
        overlap = set(text.lower().split()) & set(existing.lower().split())
        if len(overlap) / max(len(text.split()), 1) > 0.5:
            reasons.append("1.4 Биография слишком похожа на существующую.")
            break

    # Проверка структуры
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
            reasons.append(f"Отсутствует раздел: {section}")

    # ===== ИТОГ =====
    if not reasons:
        await message.answer("✅ Биография одобрена.")
    else:
        msg = "❌ Биография отклонена по причинам:\n\n"
        for r in reasons:
            msg += f"- {r}\n"
        await message.answer(msg)


# ===== WEBHOOK =====
async def on_startup(dp):
    if WEBHOOK_HOST:
        await bot.set_webhook(WEBHOOK_URL)
        print("Webhook установлен:", WEBHOOK_URL)

async def on_shutdown(dp):
    await bot.delete_webhook()


if __name__ == "__main__":
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )