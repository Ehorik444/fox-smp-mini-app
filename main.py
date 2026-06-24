from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from rcon.source import Client
from dotenv import load_dotenv
import os

# --- Загрузка переменных из .env ---
load_dotenv()

# --- Загрузка настроек из .env ---
TOKEN = " "
FORUM_CHAT_ID = os.getenv('FORUM_CHAT_ID')
THREAD_ID = int(os.getenv('THREAD_ID'))  # преобразуем в число
RCON_HOST = os.getenv('RCON_HOST')
RCON_PORT = int(os.getenv('RCON_PORT'))  # преобразуем в число
RCON_PASSWORD = os.getenv('RCON_PASSWORD')

# --- Проверка, что все переменные загружены ---
if not TOKEN or not FORUM_CHAT_ID or not RCON_PASSWORD:
    raise ValueError("Не все переменные окружения установлены в .env")

# --- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ---
bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
router = Router()

# --- ФУНКЦИЯ ДОБАВЛЕНИЯ В ВАЙТЛИСТ ЧЕРЕЗ RCON ---
def add_to_whitelist(minecraft_nick):
    try:
        with Client(RCON_HOST, RCON_PORT, passwd=RCON_PASSWORD, timeout=5) as client:
            response = client.run(f'whitelist add {minecraft_nick}')
        return True
    except Exception as e:
        print(f"Ошибка RCON: {e}")
        return False

# --- ОБРАБОТКА КОМАНДЫ /start ---
@router.message(CommandStart())
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подать заявку", callback_data='apply')]
    ])
    await message.answer("Привет! Нажми кнопку ниже, чтобы подать заявку.", reply_markup=keyboard)

# --- ОБРАБОТКА КНОПКИ "ПОДАТЬ ЗАЯВКУ" ---
@router.callback_query(F.data == 'apply')
async def process_apply(callback_query: CallbackQuery):    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "Отправь свою заявку в формате:\n\n"
        "Имя в Telegram: [ваше имя]\n"
        "Возраст: [число]\n"
        "Пол: [мужской/женский]\n"
        "Ник в Minecraft: [ник]\n"
        "О себе: [описание минимум 24 символа]"
    )

# --- ОБРАБОТКА ТЕКСТА ЗАЯВКИ ---
@router.message(F.text)
async def handle_application(message: Message):
    text = message.text.strip()

    # Парсинг заявки
    lines = text.split("\n")
    if len(lines) < 5:
        await message.reply("Неверный формат заявки.")
        return

    try:
        telegram_name = lines[0].split(": ", 1)[1]
        age = lines[1].split(": ", 1)[1]
        gender = lines[2].split(": ", 1)[1]
        minecraft_nick = lines[3].split(": ", 1)[1]
        about = lines[4].split(": ", 1)[1]

        if len(about) < 24:
            await message.reply("Поле 'о себе' должно содержать не менее 24 символов.")
            return
    except IndexError:
        await message.reply("Неверный формат заявки.")
        return

    # Формирование текста заявки
    app_text = f"""
Заявка от: {message.from_user.full_name} (@{message.from_user.username or 'N/A'})
Telegram Name: {telegram_name}
Возраст: {age}
Пол: {gender}
Ник в Minecraft: {minecraft_nick}
О себе: {about}
"""

    # Кнопки для админов
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f'accept_{message.from_user.id}_{minecraft_nick}'),            InlineKeyboardButton(text="❌ Отклонить", callback_data=f'deny_{message.from_user.id}')
        ]
    ])

    # Отправка заявки в форумную тему
    await bot.send_message(
        chat_id=FORUM_CHAT_ID,
        text=app_text,
        reply_markup=keyboard,
        message_thread_id=THREAD_ID
    )
    await message.reply("Заявка отправлена. Ожидай решения.")

# --- ОБРАБОТКА КНОПОК АДМИНА ---
@router.callback_query(F.data.startswith('accept_'))
async def accept_application(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    data = callback_query.data.split('_')
    user_id = int(data[1])
    mc_nick = data[2]

    success = add_to_whitelist(mc_nick)
    if success:
        await bot.send_message(user_id, f"✅ Поздравляю! Тебя добавили на сервер. Твой ник: {mc_nick}.")
        await bot.edit_message_reply_markup(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            message_thread_id=THREAD_ID,
            reply_markup=None
        )
    else:
        await bot.send_message(user_id, "Произошла ошибка при добавлении в вайтлист.")
        await bot.edit_message_reply_markup(
            chat_id=callback_query.message.chat.id,
            message_id=callback_query.message.message_id,
            message_thread_id=THREAD_ID,
            reply_markup=None
        )

@router.callback_query(F.data.startswith('deny_'))
async def deny_application(callback_query: CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = int(callback_query.data.split('_')[1])

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Подать новую заявку", callback_data='apply')]
    ])
    await bot.send_message(
        user_id,
        "Твоя заявка была отклонена. Можешь подать новую.",        reply_markup=keyboard
    )
    await bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        message_thread_id=THREAD_ID,
        reply_markup=None
    )

# --- ЗАПУСК БОТА ---
async def main():
    from aiogram import Dispatcher
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)

    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
