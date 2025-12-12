import os
import aiohttp
from aiogram import Bot, Dispatcher, executor, types
from dotenv import load_dotenv
from sandbox import run_code, run_tests

load_dotenv()
API_URL = os.getenv("API_URL", "http://127.0.0.1:10000/generate")  # backend сервер
TG_TOKEN = os.getenv("TG_TOKEN")

bot = Bot(TG_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler()
async def handle(msg: types.Message):
    text = msg.text

    # Выполнение кода
    if text.startswith("/run"):
        code = text[len("/run"):].strip()
        result = run_code(code)
        await msg.answer(f"Результат выполнения:\n{result}")
        return

    # Тестирование кода
    if text.startswith("/test"):
        try:
            parts = text[len("/test"):].strip().split("||")
            user_code = parts[0].strip()
            import json
            tests = json.loads(parts[1].strip())
            test_result = run_tests(user_code, tests)
            await msg.answer(f"Результаты тестов:\n{test_result}")
        except Exception as e:
            await msg.answer(f"Ошибка формата или выполнения: {e}")
        return

    # Общение через OpenAI
    async with aiohttp.ClientSession() as session:
        async with session.post(API_URL, json={"text": text}) as resp:
            data = await resp.json()
            await msg.answer(data["reply"])

if __name__ == "__main__":
    executor.start_polling(bot=bot, skip_updates=True)