import os
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from flask import Flask
import threading

TOKEN = "7998020401:AAG3D2cB4YTdxh7i2kjFXCT85wp16UV3lNU"

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Flask для Render
server = Flask(__name__)

@server.route('/')
def home():
    return "Bot is running!"

# Команда /start
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.answer("👋 Привет! Я твой стабильный бот.
Доступные команды:
/start - Приветствие
/help - Список команд
/info - Информация
/echo <текст> - Повторю твой текст")

# Команда /help
@dp.message_handler(commands=['help'])
async def help_cmd(message: types.Message):
    await message.answer("📌 Список команд:
/start - Приветствие
/help - Помощь
/info - Информация о тебе
/echo <текст> - Повторю твой текст")

# Команда /info
@dp.message_handler(commands=['info'])
async def info_cmd(message: types.Message):
    user = message.from_user
    await message.answer(f"👤 Твои данные:
ID: {user.id}
Имя: {user.first_name}")

# Команда /echo
@dp.message_handler(commands=['echo'])
async def echo_cmd(message: types.Message):
    text = message.text.replace('/echo', '').strip()
    if text:
        await message.answer(f"🔁 {text}")
    else:
        await message.answer("❌ Введи текст после команды /echo")

def start_aiogram():
    executor.start_polling(dp, skip_updates=True)

def start_flask():
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

if __name__ == "__main__":
    threading.Thread(target=start_aiogram).start()
    start_flask()
