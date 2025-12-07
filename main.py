import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv("TOKEN")  # Токен бота-генератора
bot = Bot(token=TOKEN)
dp = Dispatcher()

user_data = {}

# Шаблоны ботов
bot_templates = {
    "faq": {"description": "FAQ-Бот", "welcome": True, "auto": True, "menu": True, "custom_commands": ["help","info"]},
    "video": {"description": "Видео-Бот", "welcome": True, "auto": True, "menu": True, "custom_commands": ["video","link"]},
    "newsletter": {"description": "Рассылки-Бот", "welcome": True, "auto": False, "menu": True, "custom_commands": ["subscribe","unsubscribe"]}
}

@dp.message(Command("start"))
async def start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("FAQ-Бот", callback_data="template_faq")],
        [InlineKeyboardButton("Видео-Бот", callback_data="template_video")],
        [InlineKeyboardButton("Рассылки-Бот", callback_data="template_newsletter")]
    ])
    await message.answer("Выберите шаблон нового бота:", reply_markup=keyboard)

@dp.callback_query()
async def handle_template(query):
    uid = query.from_user.id
    template_key = query.data.replace("template_", "")
    template = bot_templates.get(template_key)
    if not template:
        await query.answer("Шаблон не найден")
        return

    user_data[uid] = {
        "template": template,
        "token": "",
        "description": "",
        "extra_menu": False,
        "extra_auto": False,
        "extra_commands": []
    }

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Добавить меню", callback_data="extra_menu")],
        [InlineKeyboardButton("Добавить автоответы", callback_data="extra_auto")],
        [InlineKeyboardButton("Добавить свои команды", callback_data="extra_commands")],
        [InlineKeyboardButton("Продолжить к описанию и токену", callback_data="continue")]
    ])
    await query.message.answer("Выберите дополнительные функции для нового бота:", reply_markup=keyboard)

@dp.callback_query()
async def handle_extras(query):
    uid = query.from_user.id
    if uid not in user_data:
        return

    data = user_data[uid]
    cb = query.data

    if cb == "extra_menu":
        data["extra_menu"] = not data["extra_menu"]
        await query.answer(f"Меню {'включено' if data['extra_menu'] else 'выключено'}")
    elif cb == "extra_auto":
        data["extra_auto"] = not data["extra_auto"]
        await query.answer(f"Автоответы {'включены' if data['extra_auto'] else 'выключены'}")
    elif cb == "extra_commands":
        await query.message.answer("Напишите свои команды через запятую, например: test, info, link")
        dp.register_message_handler(add_custom_commands, state=None, user_id=uid)
    elif cb == "continue":
        await query.message.answer("Теперь пришлите описание нового бота:")
        dp.register_message_handler(receive_description, state=None, user_id=uid)

async def add_custom_commands(message: Message):
    uid = message.from_user.id
    commands = [c.strip() for c in message.text.split(",")]
    user_data[uid]["extra_commands"].extend(commands)
    await message.answer(f"Добавлены команды: {', '.join(commands)}")
    dp.message_handlers.unregister(add_custom_commands)

async def receive_description(message: Message):
    uid = message.from_user.id
    user_data[uid]["description"] = message.text
    await message.answer("Отлично! Теперь пришлите токен нового бота (из BotFather):")
    dp.register_message_handler(receive_token, state=None, user_id=uid)
    dp.message_handlers.unregister(receive_description)

async def receive_token(message: Message):
    uid = message.from_user.id
    token = message.text
    user_data[uid]["token"] = token

    await message.answer("Создаю и запускаю нового бота...")
    await create_and_run_bot(uid)

async def create_and_run_bot(uid):
    data = user_data[uid]
    template = data["template"]
    new_bot = Bot(token=data["token"])
    new_dp = Dispatcher()

    description = data["description"]

    if template["welcome"]:
        @new_dp.message(Command("start"))
        async def start_new(message: Message):
            await message.answer(f"Привет! {description}")

    if template["auto"] or data["extra_auto"]:
        @new_dp.message()
        async def auto_response(message: Message):
            await message.answer("Вы написали: " + message.text)

    if template["menu"] or data["extra_menu"]:
        @new_dp.message(Command("menu"))
        async def menu(message: Message):
            keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
            keyboard.add("Кнопка 1","Кнопка 2")
            await message.answer("Выберите опцию:", reply_markup=keyboard)

    all_commands = template.get("custom_commands", []) + data["extra_commands"]
    for cmd in all_commands:
        @new_dp.message(Command(cmd))
        async def custom_command(message: Message, cmd=cmd):
            await message.answer(f"Вы вызвали команду /{cmd}")

    async def run_new_bot():
        from aiogram import executor
        executor.start_polling(new_dp)

    asyncio.create_task(run_new_bot())
    await bot.send_message(uid, "✅ Ваш новый бот создан и запущен! Пишите ему команды прямо сейчас.")
    user_data.pop(uid)

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp)
