import aiohttp
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

TOKEN = "8590978139:AAGIJMR9hvcScdvqjfhqaPDmEVZoSwAv3lo"
CLIENT_ID = "BUGUceypJMOS1MVyQCXccCfqKEjSnJIE"

bot = Bot(token=TOKEN)
dp = Dispatcher()


# ----------------------------------------------------
# 1. Получаем информацию о треке (новый api-v2)
# ----------------------------------------------------
async def get_track_info(url: str):
    api = f"https://api-v2.soundcloud.com/resolve?url={url}&client_id={CLIENT_ID}"

    async with aiohttp.ClientSession() as session:
        async with session.get(api, ssl=False) as resp:
            if resp.status != 200:
                print("status:", resp.status)
                return None
            return await resp.json()


# ----------------------------------------------------
# 2. Ищем MP3 progressive ссылку
# ----------------------------------------------------
async def get_mp3_url(track_info):
    trans = track_info.get("media", {}).get("transcodings", [])

    for t in trans:
        if t.get("format", {}).get("protocol") == "progressive":
            api = t["url"] + f"?client_id={CLIENT_ID}"

            async with aiohttp.ClientSession() as session:
                async with session.get(api, ssl=False) as resp:
                    if resp.status != 200:
                        continue
                    data = await resp.json()
                    return data.get("url")

    return None


# ----------------------------------------------------
# 3. Скачиваем сам MP3
# ----------------------------------------------------
async def download_mp3(url, filename):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, ssl=False) as resp:
            if resp.status != 200:
                return None

            content = await resp.read()

            with open(filename, "wb") as f:
                f.write(content)

            return filename


# ----------------------------------------------------
# 4. Команда старт
# ----------------------------------------------------
@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("Отправь ссылку SoundCloud — скачаю MP3 🎧")


# ----------------------------------------------------
# 5. Обработка ссылок
# ----------------------------------------------------
@dp.message()
async def handler(message: types.Message):
    url = message.text.strip()

    if "soundcloud.com" not in url:
        await message.answer("Это не ссылка SoundCloud ❌")
        return

    await message.answer("⏳ Получаю информацию о треке...")

    info = await get_track_info(url)
    if not info:
        await message.answer("❌ Не удалось получить данные от SoundCloud.")
        return

    title = info.get("title", "track")

    mp3_url = await get_mp3_url(info)
    if not mp3_url:
        await message.answer("❌ MP3 поток не найден (нет progressive).")
        return

    await message.answer("⏳ Скачиваю MP3...")

    filename = f"{title}.mp3"
    path = await download_mp3(mp3_url, filename)

    if not path:
        await message.answer("Ошибка скачивания ❌")
        return

    await message.answer_document(types.FSInputFile(path))


# ----------------------------------------------------
# 6. Запуск
# ----------------------------------------------------
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
