import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# 1. Bot tokeningiz
TOKEN = "8983495827:AAFnyPQwDeAKkOKjoooozLEo7XcG7T2n4B0"

# 2. Kanal username'i
CHANNEL_USERNAME = "@GOJO_Studio_Official"

# 3. Sizning Telegram ID raqamingiz (Admin)
ADMIN_IDS = [5763342144]

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Baza va linklar
ANIME_DATABASE = {}
LINK_MAP = {}

# Menyular
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Anime qidirish"), KeyboardButton(text="📚 Barcha animelar")],
        [KeyboardButton(text="🔥 Davom etayotganlar"), KeyboardButton(text="✉️ Murojaat")]
    ],
    resize_keyboard=True
)

admin_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🔍 Anime qidirish"), KeyboardButton(text="📚 Barcha animelar")],
        [KeyboardButton(text="🔥 Davom etayotganlar"), KeyboardButton(text="✉️ Murojaat")],
        [KeyboardButton(text="➕ Video qo'shish (Admin)"), KeyboardButton(text="🗑 Anime o'chirish (Admin)")]
    ],
    resize_keyboard=True    
)

cancel_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="❌ Bekor qilish")]
    ],
    resize_keyboard=True
)

poster_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="⏭ O'tkazib yuborish")],
        [KeyboardButton(text="❌ Bekor qilish")]
    ],
    resize_keyboard=True
)

finish_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text=".")],
        [KeyboardButton(text="❌ Bekor qilish")]
    ],
    resize_keyboard=True
)

# Holatlar
class AdminAnimeState(StatesGroup):
    waiting_for_anime_name = State()
    waiting_for_channel_media = State()
    waiting_for_season = State()
    waiting_for_episodes = State()

class AdminDeleteState(StatesGroup):
    waiting_for_delete_query = State()

class UserSearchState(StatesGroup):
    waiting_for_search_query = State()

class ContactState(StatesGroup):
    waiting_for_message = State()

admin_temp_data = {}

# /start komandasi
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    text = message.text.split()
    user_id = message.from_user.id
    current_menu = admin_menu if user_id in ADMIN_IDS else main_menu
    
    if len(text) > 1 and text[1].startswith("anime_"):
        link_id = text[1].replace("anime_", "")
        anime_name = LINK_MAP.get(link_id)
        
        if anime_name and anime_name in ANIME_DATABASE:
            parts = ANIME_DATABASE[anime_name]
            buttons = [
                [InlineKeyboardButton(text=f"▶️ {p.title()}", callback_data=f"w:{link_id}:{idx}")]
                for idx, p in enumerate(parts.keys())
            ]
            await message.answer(
                f"🎬 <b>{anime_name.title()}</b>\nKerakli qismni tanlang:",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
                parse_mode="HTML"
            )
            return

    await message.answer(
        f"📺 Barcha animelarni {CHANNEL_USERNAME} kanalidan toping!\n\n"
        "Bu bot haqiqiy anime muxlislari uchun! ⚡",
        reply_markup=current_menu,
        parse_mode="HTML"
    )

@dp.message(F.text == "❌ Bekor qilish")
async def cancel_process(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    current_menu = admin_menu if user_id in ADMIN_IDS else main_menu
    await message.answer("Jarayon bekor qilindi.", reply_markup=current_menu)

@dp.message(F.text == "📚 Barcha animelar")
async def show_anime_list(message: types.Message):
    if ANIME_DATABASE:
        anime_list = ""
        for name, parts in ANIME_DATABASE.items():
            anime_list += f"• <b>{name.title()}</b> ({len(parts)} ta qism)\n"
            for p in parts.keys():
                anime_list += f"   - {p.title()}\n"
        await message.answer(f"<b>Bazadagi animelar ro'yxati:</b>\n\n{anime_list}", parse_mode="HTML")
    else:
        await message.answer("Hozircha bazada animelar yo'q.")

@dp.message(F.text == "🔥 Davom etayotganlar")
async def ongoing_anime(message: types.Message):
    await message.answer(f"Yangiliklarni {CHANNEL_USERNAME} kanalidan kuzating!")

# --- MUROJAAT QISMI ---
@dp.message(F.text == "✉️ Murojaat")
async def contact_admin_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Adminlarga yubormoqchi bo'lgan murojaat, taklif yoki savolingizni yozib yuboring:",
        reply_markup=cancel_menu,
        parse_mode="HTML"
    )
    await state.set_state(ContactState.waiting_for_message)

@dp.message(ContactState.waiting_for_message)
async def send_contact_to_admin(message: types.Message, state: FSMContext):
    user = message.from_user
    # Foydalanuvchining username'ini aniqlaymiz (agar bo'lmasa ismini va ID sini chiqaramiz)
    if user.username:
        user_identifier = f"@{user.username}"
    else:
        user_identifier = f"<a href='tg://user?id={user.id}'>{user.full_name}</a>"

    contact_text = (
        f"✉️ <b>Yangi murojaat!</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {user_identifier}\n"
        f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
        f"💬 <b>Xabar:</b> {message.text}"
    )

    # Barcha adminlarga murojaatni yuboramiz
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=contact_text, parse_mode="HTML")
        except Exception as e:
            print(f"Admin (ID: {admin_id}) ga xabar yuborishda xatolik: {e}")

    user_id = message.from_user.id
    current_menu = admin_menu if user_id in ADMIN_IDS else main_menu
    
    await message.answer(
        "✅ Murojaatingiz adminga muvaffaqiyatli yuborildi! Tez orada javob berishadi.",
        reply_markup=current_menu,
        parse_mode="HTML"
    )
    await state.clear()

# --- ADMIN: Video qo'shish jarayoni ---
@dp.message(F.text == "➕ Video qo'shish (Admin)")
async def admin_add_video(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("1️⃣ <b>Anime nomini</b> yozing (masalan: <i>Naruto</i>):", reply_markup=cancel_menu, parse_mode="HTML")
    await state.set_state(AdminAnimeState.waiting_for_anime_name)

@dp.message(AdminAnimeState.waiting_for_anime_name)
async def process_anime_name(message: types.Message, state: FSMContext):
    admin_temp_data[message.from_user.id] = {
        "anime": message.text.strip().lower(),
        "uploaded_count": 0,
        "uploaded_parts": []
    }
    await message.answer("2️⃣ <b>Kanalga post uchun rasm yoki treyler video</b> yuboring:\n\n<i>(Xohlamasangiz «⏭ O'tkazib yuborish»ni bosing)</i>", reply_markup=poster_menu, parse_mode="HTML")
    await state.set_state(AdminAnimeState.waiting_for_channel_media)

@dp.message(AdminAnimeState.waiting_for_channel_media)
async def process_channel_media(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if message.text == "⏭ O'tkazib yuborish":
        admin_temp_data[user_id]["media_type"] = None
    elif message.photo:
        admin_temp_data[user_id]["media_type"] = "photo"
        admin_temp_data[user_id]["media_id"] = message.photo[-1].file_id
    elif message.video:
        admin_temp_data[user_id]["media_type"] = "video"
        admin_temp_data[user_id]["media_id"] = message.video.file_id
    else:
        await message.answer("Iltimos, rasm/video yuboring yoki o'tkazib yuborishni bosing!")
        return

    await message.answer("3️⃣ <b>Faslini</b> yozing (masalan: <i>1-fasl</i>):", reply_markup=cancel_menu, parse_mode="HTML")
    await state.set_state(AdminAnimeState.waiting_for_season)

@dp.message(AdminAnimeState.waiting_for_season)
async def process_season(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    admin_temp_data[user_id]["season"] = message.text.strip().lower()
    
    await message.answer(
        "4️⃣ Endi qismlarni ketma-ket yuboravering (Bot o'zi <b>1-qism, 2-qism...</b> deb raqamlaydi).\n\n"
        "🛑 Barcha qismlarni yuklab bo'lgach, pastdagi <b>« . »</b> tugmasini bosing yoki matn sifatida <b>.</b> yuboring.",
        reply_markup=finish_menu,
        parse_mode="HTML"
    )
    await state.set_state(AdminAnimeState.waiting_for_episodes)

@dp.message(AdminAnimeState.waiting_for_episodes)
async def process_episodes_upload(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    data = admin_temp_data.get(user_id)
    if not data:
        await state.clear()
        return

    if message.text and message.text.strip() == ".":
        anime_name = data["anime"]
        season_name = data["season"]
        uploaded_parts = data["uploaded_parts"]
        
        if not uploaded_parts:
            await message.answer("Siz hali birorta ham video yubormadingiz! Jarayon bekor qilindi.", reply_markup=admin_menu)
            await state.clear()
            return

        link_id = None
        for k, v in LINK_MAP.items():
            if v == anime_name:
                link_id = k
                break
        if link_id is None:
            link_id = str(len(LINK_MAP))
            LINK_MAP[link_id] = anime_name

        channel_status = "Kanalga yuborilmadi."
        if data.get("media_type"):
            bot_info = await bot.get_me()
            deep_link = f"https://t.me/{bot_info.username}?start=anime_{link_id}"
            
            post_caption = (
                f"🎬 <b>Yangi anime qo'shildi!</b>\n\n"
                f"🔹 <b>Anime:</b> {anime_name.title()}\n"
                f"🔹 <b>Fasl:</b> {season_name.title()}\n"
                f"🔹 <b>Qismlar soni:</b> {len(uploaded_parts)} ta\n\n"
                f"👉 Tomosha qilish uchun pastdagi tugmani bosing!\n"
                f"📢 Kanal: {CHANNEL_USERNAME}"
            )
            post_keyboard = InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="📥 Tomosha qilish", url=deep_link)]
                ]
            )
            try:
                if data["media_type"] == "photo":
                    await bot.send_photo(chat_id=CHANNEL_USERNAME, photo=data["media_id"], caption=post_caption, reply_markup=post_keyboard, parse_mode="HTML")
                elif data["media_type"] == "video":
                    await bot.send_video(chat_id=CHANNEL_USERNAME, video=data["media_id"], caption=post_caption, reply_markup=post_keyboard, parse_mode="HTML")
                channel_status = f"✅ {CHANNEL_USERNAME} kanaliga post joylandi!"
            except Exception as e:
                channel_status = f"⚠️ Kanalga yuborishda xatolik: {e}"

        await message.answer(
            f"✅ <b>Barcha qismlar muvaffaqiyatli saqlandi!</b>\n"
            f"{channel_status}\n\n"
            f"🎬 Anime: <b>{anime_name.title()}</b>\n"
            f"📌 Fasl: <b>{season_name.title()}</b>\n"
            f"📦 Jami yuklangan qismlar: {len(uploaded_parts)} ta",
            reply_markup=admin_menu,
            parse_mode="HTML"
        )
        await state.clear()
        return

    if message.video:
        data["uploaded_count"] += 1
        count = data["uploaded_count"]
        season_name = data["season"]
        anime_name = data["anime"]
        
        episode_name = f"{count}-qism"
        full_part_name = f"{season_name} {episode_name}"
        video_file_id = message.video.file_id
        
        if anime_name not in ANIME_DATABASE:
            ANIME_DATABASE[anime_name] = {}
        ANIME_DATABASE[anime_name][full_part_name] = video_file_id
        
        data["uploaded_parts"].append(full_part_name)
        
        await message.answer(
            f"✅ <b>{full_part_name.title()}</b> qabul qilindi va saqlandi!\n"
            f"Keyingi qismni yuboring yoki tugatish uchun <b> « . » </b> tugmasini bosing.",
            reply_markup=finish_menu,
            parse_mode="HTML"
        )
    else:
        await message.answer("Iltimos, video yuboring yoki tugatish uchun <b> « . » </b> tugmasini bosing!", parse_mode="HTML", reply_markup=finish_menu)

# --- ADMIN: O'chirish ---
@dp.message(F.text == "🗑 Anime o'chirish (Admin)")
async def admin_delete_start(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    if not ANIME_DATABASE:
        await message.answer("Hozircha bazada animelar yo'q.", reply_markup=admin_menu)
        return
    await message.answer("O'chirish uchun yozing (Masalan: <code>naruto / 1-fasl 1-qism</code> yoki faqat <code>naruto</code>):", reply_markup=cancel_menu, parse_mode="HTML")
    await state.set_state(AdminDeleteState.waiting_for_delete_query)

@dp.message(AdminDeleteState.waiting_for_delete_query)
async def process_delete(message: types.Message, state: FSMContext):
    text = message.text.strip().lower()
    if "/" in text:
        parts = text.split("/")
        anime_name, part_name = parts[0].strip(), parts[1].strip()
        if anime_name in ANIME_DATABASE and part_name in ANIME_DATABASE[anime_name]:
            del ANIME_DATABASE[anime_name][part_name]
            if not ANIME_DATABASE[anime_name]:
                del ANIME_DATABASE[anime_name]
            await message.answer("✅ O'chirildi!", reply_markup=admin_menu)
        else:
            await message.answer("❌ Topilmadi.", reply_markup=admin_menu)
    else:
        if text in ANIME_DATABASE:
            del ANIME_DATABASE[text]
            await message.answer("✅ Butunlay o'chirildi!", reply_markup=admin_menu)
        else:
            await message.answer("❌ Topilmadi.", reply_markup=admin_menu)
    await state.clear()

# --- FOYDALANUVCHI: Qidirish ---
@dp.message(F.text == "🔍 Anime qidirish")
async def cmd_search_start(message: types.Message, state: FSMContext):
    await message.answer("Qidirmoqchi bo'lgan anime nomini yozing:", reply_markup=cancel_menu, parse_mode="HTML")
    await state.set_state(UserSearchState.waiting_for_search_query)

@dp.message(UserSearchState.waiting_for_search_query)
async def process_search(message: types.Message, state: FSMContext):
    query = message.text.strip().lower()
    user_id = message.from_user.id
    current_menu = admin_menu if user_id in ADMIN_IDS else main_menu
    
    matched_animes = [name for name in ANIME_DATABASE.keys() if query in name]
    if matched_animes:
        anime_name = matched_animes[0]
        parts = ANIME_DATABASE[anime_name]
        
        link_id = None
        for k, v in LINK_MAP.items():
            if v == anime_name:
                link_id = k
                break
        if link_id is None:
            link_id = str(len(LINK_MAP))
            LINK_MAP[link_id] = anime_name

        buttons = [
            [InlineKeyboardButton(text=f"▶️ {p.title()}", callback_data=f"w:{link_id}:{idx}")]
            for idx, p in enumerate(parts.keys())
        ]
        await message.answer(f"🎬 <b>{anime_name.title()}</b> topildi! Qismni tanlang:", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
        await message.answer("Asosiy menyu:", reply_markup=current_menu)
    else:
        await message.answer("Kechirasiz, topilmadi.", reply_markup=current_menu)
    await state.clear()

@dp.callback_query(F.data.startswith("w:"))
async def send_selected_episode(callback: CallbackQuery):
    _, link_id, idx_str = callback.data.split(":", 2)
    anime_name = LINK_MAP.get(link_id)
    
    if anime_name and anime_name in ANIME_DATABASE:
        parts_list = list(ANIME_DATABASE[anime_name].items())
        idx = int(idx_str)
        if 0 <= idx < len(parts_list):
            part_name, file_id = parts_list[idx]
            await callback.message.answer_video(
                video=file_id,
                caption=f"🎬 <b>{anime_name.title()}</b>\n📌 <b>{part_name.title()}</b>\n\n📢 Kanal: {CHANNEL_USERNAME}",
                parse_mode="HTML"
            )
            await callback.answer()
            return
            
    await callback.answer("Video topilmadi!", show_alert=True)

async def main():
    logging.basicConfig(level=logging.INFO)
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())