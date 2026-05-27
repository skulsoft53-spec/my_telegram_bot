import asyncio
import os
import time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
import yt_dlp

TOKEN = os.getenv("TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# сколько видео одновременно скачивать
semaphore = asyncio.Semaphore(3)

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "👋 Отправь ссылку TikTok и я скачаю видео"
    )

@dp.message()
async def download_video(message: types.Message):

    url = message.text

    if "tiktok.com" not in url:
        await message.answer("❌ Это не TikTok ссылка")
        return

    async with semaphore:

        await message.answer("📥 Скачиваю видео...")

        filename = f"{message.from_user.id}_{int(time.time())}.mp4"

        ydl_opts = {
            "outtmpl": filename,
            "format": "mp4",
            "socket_timeout": 15,
            "noplaylist": True,
            "quiet": True
        }

        try:

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            video = types.FSInputFile(filename)

            await message.answer_video(
                video,
                caption="✅ Готово"
            )

        except Exception as e:
            await message.answer(
                f"❌ Ошибка загрузки\n\n{e}"
            )

        finally:

            if os.path.exists(filename):
                os.remove(filename)

async def main():
    print("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())