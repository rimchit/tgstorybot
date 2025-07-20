
import os
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.utils.markdown import hbold
from dotenv import load_dotenv

# Load env variables
load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
API_KEY = os.getenv("API_KEY")
API_URL = 'https://story.blindzone.org/get_stories_by_username'
BASE_URL = 'https://story.blindzone.org/'

# Bot setup
bot = Bot(token=API_TOKEN)
dp = Dispatcher()

# Temporary storage for usernames
usernames = {}


# === Story Fetching ===
async def fetch_stories(username: str, archive: bool = False):
    params = {
        'api_key': API_KEY,
        'username': username,
        'archive': str(archive).lower(),
        'mark': 'false'
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(API_URL, params=params, timeout=10) as response:
                response.raise_for_status()
                return await response.json()
    except Exception as e:
        print(f"[API ERROR] {e}")
        return None


# === Inline Buttons ===
def get_mode_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👀 Bugungi hikoyalar", callback_data="mode_today")],
        [InlineKeyboardButton(text="📦 Arxiv hikoyalar", callback_data="mode_archive")]
    ])


def get_back_button():
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🔙 Orqaga", callback_data="go_back")]]
    )


# === /start handler ===
@dp.message(CommandStart())
async def start_handler(message: types.Message):
    await message.answer(
        "👋 Salom! Menga istalgan Telegram foydalanuvchisining @usernameni yuboring, "
        "men sizga hikoyalarini topishga yordam beraman."
    )


# === @username yuborilganda ===
@dp.message(F.text.startswith('@'))
async def username_handler(message: types.Message):
    username = message.text[1:]
    user_id = message.from_user.id
    usernames[user_id] = username

    data = await fetch_stories(username, archive=False)
    views_today = data.get("views_today", 0) if data else 0

    await message.answer(
        f"{hbold('Foydalanuvchi:')} @{username}
"
        f"📊 {hbold('Bugungi hikoya ko‘rishlar:')} {views_today}

"
        "👇 Qaysi turdagi hikoyani ko‘rmoqchisiz?",
        reply_markup=get_mode_buttons()
    )


# === Callbacklar ===
@dp.callback_query(F.data.startswith("mode_"))
async def callback_handler(call: CallbackQuery):
    mode = call.data.split("_")[1]
    user_id = call.from_user.id
    username = usernames.get(user_id)

    if not username:
        await call.message.edit_text("❗ Username topilmadi. Avval @username yuboring.")
        return

    archive = (mode == "archive")
    await call.message.edit_text("🔍 Hikoyalar izlanmoqda...")

    data = await fetch_stories(username, archive)

    if data and data.get('ok') and data.get('stories'):
        count = 0
        for story in data['stories'][:5]:
            url_path = story.get('url')
            if url_path:
                full_url = BASE_URL + url_path
                try:
                    await call.message.answer_video(video=full_url)
                except:
                    await call.message.answer(full_url)
                count += 1

        if count == 0:
            await call.message.answer("🚫 Video mavjud emas.", reply_markup=get_back_button())
        else:
            await call.message.answer("✅ Yana tanlash uchun quyidagi tugmani bosing:", reply_markup=get_back_button())
    else:
        await call.message.answer("🚫 Hikoyalar topilmadi.", reply_markup=get_back_button())


@dp.callback_query(F.data == "go_back")
async def go_back_handler(call: CallbackQuery):
    user_id = call.from_user.id
    username = usernames.get(user_id)

    if not username:
        await call.message.edit_text("❗ Username topilmadi. Avval @username yuboring.")
        return

    data = await fetch_stories(username, archive=False)
    views_today = data.get("views_today", 0) if data else 0

    await call.message.edit_text(
        f"{hbold('Foydalanuvchi:')} @{username}
"
        f"📊 {hbold('Bugungi hikoya ko‘rishlar:')} {views_today}

"
        "👇 Qaysi turdagi hikoyani ko‘rmoqchisiz?",
        reply_markup=get_mode_buttons()
    )


# === Bot ishga tushirish ===
async def main():
    print("✅ Bot ishga tushdi!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
