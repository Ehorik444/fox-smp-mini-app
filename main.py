import asyncio
import os
from dotenv import load_dotenv
from aiogram import Router, Bot, F, Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from mcrcon import MCRcon

# Загрузка настроек
load_dotenv()

TOKEN = "8644843971:AAHOzQ-fT8FkhJ3oshAZE61ZBVc3lgjM-ps"
FORUM_CHAT_ID = os.getenv('FORUM_CHAT_ID')
THREAD_ID = int(os.getenv('THREAD_ID', 0))
RCON_HOST = os.getenv('RCON_HOST')
RCON_PORT = int(os.getenv('RCON_PORT', 25575))
RCON_PASSWORD = os.getenv('RCON_PASSWORD')

# Инициализация бота (aiogram 3.x)
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
router = Router()

def sync_add_to_whitelist(minecraft_nick):
    """Работа с Minecraft через mcrcon"""
    try:
        with MCRcon(RCON_HOST, RCON_PASSWORD, port=RCON_PORT, timeout=10) as mcr:
            mcr.command(f"whitelist add {minecraft_nick}")
        return True
    except Exception as e:
        print(f"Ошибка RCON: {e}")
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
        "📝 Отправь заявку СТРОГО в таком формате:\n\n"
        "Имя: Иван\nВозраст: 20\nПол: Мужской\nНик в Minecraft: Steve\nО себе: Играю долго, адекватный"
    )

@router.message(F.text)
async def handle_application(message: Message):
    if str(message.chat.id) == str(FORUM_CHAT_ID): return
    
    lines = message.text.split("\n")
    if len(lines) < 4:
        await message.reply("❌ Неверный формат заявки.")
        return

    mc_nick = ""
    for line in lines:
        if "Ник в Minecraft:" in line:
            mc_nick = line.split(":", 1)[1].strip()
    
    if not mc_nick:
        await message.reply("❌ Введите 'Ник в Minecraft: ваш_ник'")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Принять", callback_data=f"accept_{message.from_user.id}"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data=f"deny_{message.from_user.id}")
        ]
    ])

    await bot.send_message(
        chat_id=FORUM_CHAT_ID,
        message_thread_id=THREAD_ID,
        text=f"⚡️ <b>Новая заявка!</b>\n\n{message.text}\n\n👤 От: {message.from_user.mention_html()}",
        reply_markup=keyboard
    )
    await message.reply("✅ Заявка отправлена!")

@router.callback_query(F.data.startswith('accept_'))
async def accept_app(callback: CallbackQuery):
    user_id = int(callback.data.split('_')[1])
    mc_nick = ""
    for line in callback.message.text.split("\n"):
        if "Ник в Minecraft:" in line: mc_nick = line.split(":", 1)[1].strip()

    if await add_to_whitelist(mc_nick):
        try: await bot.send_message(user_id, f"✅ Тебя добавили в вайтлист! Ник: {mc_nick}")
        except: pass
        await callback.message.edit_text(callback.message.text + "\n\n🟢 ПРИНЯТ", reply_markup=None)
    else:
        await callback.answer("Ошибка RCON! Проверь консоль.", show_alert=True)

@router.callback_query(F.data.startswith('deny_'))
async def deny_app(callback: CallbackQuery):
    user_id = int(callback.data.split('_')[1])
    try: await bot.send_message(user_id, "❌ Твоя заявка отклонена.")
    except: pass
    await callback.message.edit_text(callback.message.text + "\n\n🔴 ОТКЛОНЕН", reply_markup=None)

async def main():
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
