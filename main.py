import asyncio
import os
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
    from mcrcon import MCRcon
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT, timeout=10) as mcr:
            mcr.command(f"whitelist add {minecraft_nick}")
        return True
    except Exception as e:
        print(f"MCRcon Error: {e}")
        return False

async def add_to_whitelist(nick):
    return await asyncio.to_thread(sync_add_to_whitelist, nick)

@router.message(CommandStart())
async def cmd_start(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Подать заявку", callback_data='apply')]
    ])
    await message.answer("Привет! Нажми кнопку ниже, чтобы подать заявку.", reply_markup=keyboard)

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# Описываем шаги анкеты
class Form(StatesGroup):
    name = State()
    age = State()
    gender = State()
    mc_nick = State()
    about = State()

@router.callback_query(F.data == 'apply')
async def start_form(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(Form.name)
    await callback.message.answer("1. Как тебя зовут?")

@router.message(Form.name)
async def proc_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(Form.age)
    await message.answer("2. Сколько тебе лет?")

@router.message(Form.age)
async def proc_age(message: Message, state: FSMContext):
    if not message.text.isdigit():
        return await message.answer("Пожалуйста, введи возраст числом.")
    await state.update_data(age=message.text)
    await state.set_state(Form.gender)
    await message.answer("3. Твой пол?")

@router.message(Form.gender)
async def proc_gender(message: Message, state: FSMContext):
    await state.update_data(gender=message.text)
    await state.set_state(Form.mc_nick)
    await message.answer("4. Твой ник в Minecraft?")

@router.message(Form.mc_nick)
async def proc_nick(message: Message, state: FSMContext):
    await state.update_data(mc_nick=message.text)
    await state.set_state(Form.about)
    await message.answer("5. Расскажи немного о себе (минимум 20 символов).")

@router.message(Form.about)
async def proc_about(message: Message, state: FSMContext):
    if len(message.text) < 20:
        return await message.answer("Напиши чуть подробнее (минимум 20 символов).")
    
    data = await state.get_data()
    summary = (
        f"📋 Новая заявка!\n\n"
        f"Имя: {data['name']}\n"
        f"Возраст: {data['age']}\n"
        f"Пол: {data['gender']}\n"
        f"Ник MC: {data['mc_nick']}\n"
        f"О себе: {message.text}\n\n"
        f"👤 Отправитель: {message.from_user.mention_html()}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"acc_{message.from_user.id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"den_{message.from_user.id}")
        ]
    ])

    await bot.send_message(FORUM_CHAT_ID, summary, message_thread_id=THREAD_ID, reply_markup=kb)
    await message.answer("✅ Готово! Твоя заявка отправлена админам.")
    await state.clear()

# Обработка кнопок админа
@router.callback_query(F.data.startswith('acc_'))
async def admin_accept(callback: CallbackQuery):
    user_id = int(callback.data.split('_')[1])
    # Извлекаем ник из текста (он между 'Ник MC:' и новой строкой)
    mc_nick = callback.message.text.split("Ник MC:")[1].split("\n")[0].strip()
    
    await callback.answer("⏳ Добавляю...")
    success = await add_to_whitelist(mc_nick)

    if success:
        try: await bot.send_message(user_id, f"✅ Ваша заявка одобрена! Ник {mc_nick} добавлен в вайтлист.")
        except: pass
        await callback.message.edit_text(callback.message.text + "\n\n🟢 СТАТУС: ПРИНЯТ", reply_markup=None)
    else:
        await callback.answer("Ошибка RCON", show_alert=True)

@router.callback_query(F.data.startswith('den_'))
async def admin_deny(callback: CallbackQuery):
    user_id = int(callback.data.split('_')[1])
    try: await bot.send_message(user_id, "❌ Ваша заявка была отклонена.")
    except: pass
    await callback.message.edit_text(callback.message.text + "\n\n🔴 СТАТУС: ОТКЛОНЕН", reply_markup=None)
    await callback.answer("Отклонено")

async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
                    
