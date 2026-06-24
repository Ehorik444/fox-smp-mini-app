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

@router.callback_query(F.data == 'apply')
async def process_apply(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "📝 Отправь свою заявку СТРОГО в таком формате (скопируй и заполни):\n\n"
        "Имя: Иван\n"
        "Возраст: 20\n"
        "Пол: Мужской\n"
        "Ник в Minecraft: Steve\n"
        "О себе: Играю в майнкрафт более пяти лет, адекватный и спокойный."
    )

@router.message(F.text)
async def handle_application(message: Message):
    # Если это сообщение в чате админов - игнорируем
    if str(message.chat.id) == str(FORUM_CHAT_ID):
        return

    text = message.text.strip()
    lines = text.split("\n")
    
    if len(lines) < 5:
        await message.reply("❌ Неверный формат. Нужно заполнить все 5 строк.")
        return

    try:
        # Безопасное извлечение ника (4-я строка)
        mc_nick = lines[3].split(":", 1)[1].strip()
        about = lines[4].split(":", 1)[1].strip()

        if len(about) < 24:
            await message.reply("❌ Описание 'О себе' должно быть не меньше 24 символов.")
            return
            
        # Кнопки для админов (передаем user_id)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_{message.from_user.id}"),
                InlineKeyboardButton(text="❌ Отклонить", callback_data=f"deny_{message.from_user.id}")
            ]
        ])

        await bot.send_message(
            chat_id=FORUM_CHAT_ID,
            message_thread_id=THREAD_ID,
            text=f"⚡️ Новая заявка!\n\n{text}\n\n👤 От: {message.from_user.mention_html()}\n🆔 ID: {message.from_user.id}",
            reply_markup=keyboard
        )
        await message.reply("✅ Твоя заявка отправлена на рассмотрение. Ожидай ответа!")
        
    except Exception as e:
        await message.reply("❌ Ошибка в формате. Проверь наличие двоеточий ':' в каждой строке.")

# Обработка принятия
@router.callback_query(F.data.startswith('accept_'))
async def accept_application(callback: CallbackQuery):
    user_id = int(callback.data.split('_')[1])
    
    # Достаем ник из текста заявки (он в 4-й строке)
    lines = callback.message.text.split("\n")
    mc_nick = ""
    for line in lines:
        if "Ник в Minecraft:" in line:
            mc_nick = line.split(":", 1)[1].strip()
            break

    if not mc_nick:
        await callback.answer("Не удалось найти ник в сообщении!", show_alert=True)
        return

    await callback.answer("⏳ Добавляю в вайтлист...")
    success = await add_to_whitelist(mc_nick)

    if success:
        try:
            await bot.send_message(user_id, f"🥳 Поздравляем!\nВаша заявка одобрена. Вы добавлены в вайтлист под ником: {mc_nick}.")
        except Exception: pass
        
        await callback.message.edit_text(callback.message.text + "\n\n🟢 СТАТУС: ПРИНЯТ", reply_markup=None)
    else:
        await callback.message.answer("❌ Ошибка RCON при добавлении!")

# Обработка отклонения
@router.callback_query(F.data.startswith('deny_'))
async def deny_application(callback: CallbackQuery):
    user_id = int(callback.data.split('_')[1])
    try:
        await bot.send_message(user_id, "❌ К сожалению, ваша заявка была отклонена администрацией.")
    except Exception: pass
    
    await callback.message.edit_text(callback.message.text + "\n\n🔴 СТАТУС: ОТКЛОНЕН", reply_markup=None)
    await callback.answer("Заявка отклонена")

async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
                    
