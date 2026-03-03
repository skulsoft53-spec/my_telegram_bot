import os
import re
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ParseMode
from aiogram.utils import executor
from spellchecker import SpellChecker

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Укажите BOT_TOKEN в переменных окружения")

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

spell = SpellChecker(language='ru')

# Пример существующих биографий для проверки уникальности
existing_biographies_texts = [
    "Пример текста уже поданной биографии..."
]

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer(
        "Привет! Отправь свою RP-биографию.\n"
        "Формат заголовка: Биография | Nick_Name\n"
        "Последняя строка должна содержать Font и Size, например:\n"
        "Font=Times New Roman|Size=15\n"
        "Фото: укажи 'Фото: есть'\n"
        "После проверки бот вернёт отчёт с ошибками и рекомендациями."
    )

@dp.message()
async def check_biography(message: types.Message):
    text = message.text
    if not text:
        await message.answer("❌ Пустое сообщение.")
        return
    
    lines = text.split('\n')
    if len(lines) < 3:
        await message.answer("❌ Слишком короткая биография.")
        return
    
    title = lines[0].strip()
    font_info_line = lines[-1].strip()
    font_info = {'font': '', 'size': 0}
    font_match = re.search(r'Font=([\w\s]+)\|Size=(\d+)', font_info_line, re.IGNORECASE)
    if font_match:
        font_info['font'] = font_match.group(1).strip()
        font_info['size'] = int(font_match.group(2))
        body_lines = lines[1:-1]
    else:
        body_lines = lines[1:]

    body_text = '\n'.join(body_lines)
    photos_attached = 'фото: есть' in text.lower()
    result = validate_biography(title, body_text, font_info, photos_attached, existing_biographies_texts)
    await message.answer(result, parse_mode=ParseMode.MARKDOWN)

def validate_biography(title, text, font_info, photos_attached, existing_texts):
    results = []
    words = re.findall(r'\w+', text, flags=re.UNICODE)
    word_count = len(words)

    if re.match(r'^Биография \| \w+$', title):
        results.append("✅ Заголовок корректен")
    else:
        results.append("❌ Заголовок должен быть: 'Биография | Nick_Name'")

    if 200 <= word_count <= 600:
        results.append(f"✅ Объем текста: {word_count} слов")
    elif word_count < 200:
        results.append(f"❌ Слишком мало слов: {word_count} (минимум 200)")
    else:
        results.append(f"❌ Слишком много слов: {word_count} (максимум 600)")

    misspelled = spell.unknown([w.lower() for w in words])
    if misspelled:
        sample = ', '.join(list(misspelled)[:5])
        results.append(f"❌ Орфографические ошибки: {len(misspelled)} слов. Примеры: {sample}")
    else:
        results.append("✅ Орфография без ошибок")

    allowed_fonts = ['Times New Roman', 'Verdana']
    if font_info.get('font') in allowed_fonts and font_info.get('size', 0) >= 15:
        results.append(f"✅ Шрифт {font_info['font']}, размер {font_info['size']} корректны")
    else:
        results.append("❌ Шрифт должен быть Times New Roman или Verdana, размер ≥ 15")

    if photos_attached:
        results.append("✅ Фото приложены")
    else:
        results.append("❌ Фото отсутствуют")

    duplicate = False
    for existing in existing_texts:
        existing_words = set(re.findall(r'\w+', existing.lower()))
        overlap = set(w.lower() for w in words) & existing_words
        if len(overlap) / max(len(words), 1) > 0.5:
            duplicate = True
            break
    if duplicate:
        results.append("❌ Биография слишком похожа на существующую")
    else:
        results.append("✅ Биография уникальна")

    if all(r.startswith("✅") for r in results):
        status = "✅ Заявка одобрена ✔️"
    else:
        status = "❌ Заявка отклонена ❌"
    results.append(f"\nСтатус: {status}")

    return "\n".join(results)

if __name__ == "__main__":
    from aiogram.utils import executor
    executor.start_polling(dp, skip_updates=True)
