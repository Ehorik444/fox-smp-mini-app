import asyncio
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from rcon.source import Client

# --- НАСТРОЙКИ ---
TOKEN = '8330996067:AAGxj7bpdoFcEMuShmyd1MKuI2hJXq5IU3k'
FORUM_CHAT_ID = '-1003255144076'
THREAD_ID = 3567  # ID темы в форуме
RCON_HOST = 'c11.play2go.cloud'
RCON_PORT = 20722
RCON_PASSWORD = 'hfyG4v5SShHNLZhlVOtTZ0TotBvenJZtEkOuASq4MlsOZLYQ8stXFbbrblFvOWOeVjyU6o5TWu1WahKnKNJShXoIUEhsTbEPLDG'

# --- ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ---
storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)

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
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Подать заявку", callback_data='apply')
    )
    await message.answer("Привет! Нажми кнопку ниже, чтобы подать заявку.", reply_markup=keyboard)

# --- ОБРАБОТКА КНОПКИ "ПОДАТЬ ЗАЯВКУ" ---
@dp.callback_query_handler(lambda c: c.data == 'apply')
async def process_apply(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(
        callback_query.from_user.id,
        "Отправь свою заявку в формате:\n\n"
        "Имя в Telegram: [ваше имя]\n"
        "Возраст: [число]\n"
        "Пол: [мужской/женский]\n"
        "Ник в Minecraft: [ник]\n"        "О себе: [описание минимум 24 символа]"
    )

# --- ОБРАБОТКА ТЕКСТА ЗАЯВКИ ---
@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def handle_application(message: types.Message):
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
    keyboard = InlineKeyboardMarkup().row(
        InlineKeyboardButton("✅ Принять", callback_data=f'accept_{message.from_user.id}_{minecraft_nick}'),
        InlineKeyboardButton("❌ Отклонить", callback_data=f'deny_{message.from_user.id}')
    )

    # Отправка заявки в форумную тему
    await bot.send_message(
        chat_id=FORUM_CHAT_ID,
        text=app_text,
        reply_markup=keyboard,
        message_thread_id=THREAD_ID  # <-- Указывает на конкретную тему в форуме    )
    await message.reply("Заявка отправлена. Ожидай решения.")

# --- ОБРАБОТКА КНОПОК АДМИНА ---
@dp.callback_query_handler(lambda c: c.data.startswith('accept_'))
async def accept_application(callback_query: types.CallbackQuery):
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
            message_thread_id=THREAD_ID,  # <-- Обязательно указываем thread_id
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

@dp.callback_query_handler(lambda c: c.data.startswith('deny_'))
async def deny_application(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    user_id = int(callback_query.data.split('_')[1])

    keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton("Подать новую заявку", callback_data='apply')
    )
    await bot.send_message(
        user_id,
        "Твоя заявка была отклонена. Можешь подать новую.",
        reply_markup=keyboard
    )
    await bot.edit_message_reply_markup(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.message_id,
        message_thread_id=THREAD_ID,  # <-- Обязательно указываем thread_id
        reply_markup=None
    )

if __name__ == '__main__':    executor.start_polling(dp, skip_updates=True)
