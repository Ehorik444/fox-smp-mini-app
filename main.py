import asyncio
import os
import dotenv
from dotenv import load_dotenv
from aiogram import Router, Bot, F, Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from rcon.source import Client

load_dotenv()

TOKEN = "ВАШ_ТОКЕН"
FORUM_CHAT_ID = os.getenv('FORUM_CHAT_ID')
THREAD_ID = int(os.getenv('THREAD_ID', 0))
RCON_HOST = os.getenv('RCON_HOST')
RCON_PORT = int(os.getenv('RCON_PORT', 25575))
RCON_PASSWORD = os.getenv('RCON_PASSWORD')

# Инициализация с использованием DefaultBotProperties
bot = Bot(
    token=TOKEN, 
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
router = Router()

# Делаем RCON асинхронным через asyncio.to_thread
def sync_add_to_whitelist(minecraft_nick):
    try:
        with Client(RCON_HOST, RCON_PORT, passwd=RCON_PASSWORD, timeout=5) as client:
            client.run(f'whitelist add {minecraft_nick}')
        return True
    except Exception as e:
        print(f"RCON Error: {e}")
        return False

async def add_to_whitelist(nick):
    return await asyncio.to_thread(sync_add_to_whitelist, nick)

@router.message(CommandStart())
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Подать заявку", callback_data='apply')]
    ])
    await message.answer("Привет! Нажми кнопку ниже, чтобы подать заявку.", reply_markup=keyboard)

@router.callback_query(F.data == 'apply')
async def process_apply(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Отправь заявку СТРОГО в этом формате:\n\n"
        "Имя: Иван\nВозраст: 20\nПол: Мужской\nНик: Steve\nО себе: Играю долго, адекватный"
    )

@router.message(F.text)
async def handle_application(message: Message):
    # Улучшенный парсинг
    lines = message.text.split('\n')
    if len(lines) < 5:
        await message.reply("❌ Неверный формат. Нужно 5 строк.")
        return

    try:
        nick = lines[3].split(':')[1].strip()
        about = lines[4].split(':')[1].strip()
        
        if len(about) < 24:
            await message.reply("❌ О себе должно быть > 24 символов.")
            return
            
        # Формируем callback_data аккуратно (лимит 64 байта)
        # Используем только ID пользователя
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                # ВАЖНО: Храним ник в самом тексте кнопки или БД, если он длинный
                InlineKeyboardButton(text="✅ Принять", callback_data=f"acc_{message.from_user.id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"den_{message.from_user.id}")
            ]
        ])

        await bot.send_message(
            chat_id=FORUM_CHAT_ID,
            message_thread_id=THREAD_ID,
            text=f"Новая заявка!\n{message.text}\nID: {message.from_user.id}",
            reply_markup=keyboard
        )
        await message.reply("⏳ Заявка отправлена!")
        
    except Exception:
        await message.reply("❌ Ошибка в формате.")

# Для примера упростим логику получения ника (лучше использовать Redis/FSM)
@router.callback_query(F.data.startswith('acc_'))
async def accept_app(callback: CallbackQuery):
    user_id = int(callback.data.split('_')[1])
    # Извлекаем ник из текста сообщения
    lines = callback.message.text.split('\n')
    mc_nick = "unknown"
    for line in lines:
        if "Ник:" in line: mc_nick = line.split(':')[1].strip()

    success = await add_to_whitelist(mc_nick)
    
    if success:
        await bot.send_message(user_id, f"✅ Вы добавлены! Ник: {mc_nick}")
        await callback.message.edit_text(callback.message.text + "\n\nСТАТУС: ПРИНЯТ")
    else:
        await callback.answer("Ошибка RCON", show_alert=True)

async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
                    
