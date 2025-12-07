import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiohttp import web

TOKEN = os.getenv("TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_URL")  # https://your-service-name.onrender.com
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = WEBHOOK_HOST + WEBHOOK_PATH

bot = Bot(token=TOKEN)
dp = Dispatcher()

user_links = {}  # временное хранилище


def main_menu():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="📁 Мои ссылки", callback_data="links")],
        [types.InlineKeyboardButton(text="🧹 Очистить историю", callback_data="clear")],
        [types.InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")]
    ])


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 Привет! Отправь мне видео — я дам красивую прямую ссылку.\n",
        reply_markup=main_menu()
    )


@dp.message(F.video)
async def handle_video(message: types.Message):
    user_id = message.from_user.id
    file = await bot.get_file(message.video.file_id)
    link = f"https://api.telegram.org/file/bot{TOKEN}/{file.file_path}"
    user_links.setdefault(user_id, []).append(link)

    await message.answer(f"🎉 Готово!\n🔗 {link}", reply_markup=main_menu())


@dp.callback_query(F.data == "links")
async def show_links(callback):
    user_id = callback.from_user.id
    links = user_links.get(user_id, [])

    if not links:
        await callback.message.edit_text("📁 У тебя нет сохранённых ссылок.", reply_markup=main_menu())
        return

    text = "📁 Твои ссылки:\n\n" + "\n".join(f"{i+1}. {l}" for i, l in enumerate(links))
    await callback.message.edit_text(text, reply_markup=main_menu())


@dp.callback_query(F.data == "clear")
async def clear_links(callback):
    user_links[callback.from_user.id] = []
    await callback.message.edit_text("🧹 История очищена!", reply_markup=main_menu())


@dp.callback_query(F.data == "help")
async def help_menu(callback):
    await callback.message.edit_text(
        "ℹ️ Отправь мне видео — я дам прямую ссылку.\nВсе ссылки в меню → 📁 Мои ссылки",
        reply_markup=main_menu()
    )

# --- WEBHOOK SERVER ---

async def handle_webhook(request):
    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(bot, update)
    return web.Response()

async def health(request):
    return web.Response(text="OK")

async def on_startup(app):
    await bot.set_webhook(WEBHOOK_URL)

async def on_shutdown(app):
    await bot.delete_webhook()

def start():
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, handle_webhook)
    app.router.add_get("/", health)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    web.run_app(app, port=int(os.getenv("PORT", 8000)))

if __name__ == "__main__":
    start()