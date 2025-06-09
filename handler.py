### handler.py
import os
from aiogram import Router, F, Bot
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, FSInputFile, InputMediaPhoto
)
from loguru import logger
from pathlib import Path
from prompts import get_answer

AGENT_BOT_TOKEN = os.getenv("AGENT_BOT_TOKEN")
TG_CHAT_LEAD = os.getenv("TG_CHAT_LEAD")

if not AGENT_BOT_TOKEN:
    raise EnvironmentError("❌ AGENT_BOT_TOKEN не задан")
if not TG_CHAT_LEAD:
    raise EnvironmentError("❌ TG_CHAT_LEAD не задан")

bot = Bot(token=AGENT_BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
router = Router()

user_states = {}

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="📁 Получить КП")],
            [KeyboardButton(text="📷 Фото объекта")],
            [KeyboardButton(text="📝 Оставить заявку")],
        ]
    )

@router.message(F.text.lower() == "/start")
async def start_handler(msg: Message):
    logger.info(f"▶️ /start от {msg.from_user.id}")
    await msg.answer(
        "👋 Добро пожаловать! Я — Telegram-ассистент по продаже уникального объекта.\n\n"
        "📑 Получить КП\n📷 Фото объекта\n📝 Оставить заявку\n\n"
        "📩 Или просто задайте вопрос — я отвечу!",
        reply_markup=get_main_keyboard()
    )

@router.message(F.text == "📁 Получить КП")
async def send_presentation(msg: Message):
    folder = "templates"
    try:
        files = sorted(Path(folder).glob("*.pdf"))
        if not files:
            await msg.answer("❌ Документы не найдены.")
            return
        await msg.answer("📎 Отправляю документы:")
        for doc in files:
            await msg.answer_document(FSInputFile(doc))
    except Exception as e:
        logger.error(f"Ошибка отправки КП: {e}")
        await msg.answer("⚠️ Не удалось отправить документы.")

@router.message(F.text == "📷 Фото объекта")
async def send_photos(msg: Message):
    folder = "images"
    try:
        if not os.path.exists(folder):
            await msg.answer("❌ Папка с фото не найдена.")
            return
        media = [InputMediaPhoto(FSInputFile(os.path.join(folder, f))) for f in os.listdir(folder)
                 if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        if not media:
            await msg.answer("📂 Фото не найдены.")
            return
        for i in range(0, len(media), 10):
            await msg.answer_media_group(media[i:i+10])
    except Exception as e:
        logger.error(f"Ошибка отправки фото: {e}")
        await msg.answer("⚠️ Ошибка при отправке фото.")

@router.message(F.text == "📝 Оставить заявку")
async def start_form(msg: Message):
    user_states[msg.from_user.id] = {"step": "name"}
    await msg.answer("✍️ Введите ваше ФИО:")

@router.message(F.text)
async def handle_message(msg: Message):
    user_id = msg.from_user.id
    state = user_states.get(user_id)

    if state:
        if state["step"] == "name":
            state["name"] = msg.text.strip()
            state["step"] = "phone"
            await msg.answer("📞 Введите номер телефона:")
            return
        elif state["step"] == "phone":
            phone = msg.text.strip()
            state["phone"] = phone
            await bot.send_message(TG_CHAT_LEAD, f"📥 Заявка\nФИО: {state['name']}\nТелефон: {phone}")
            user_states.pop(user_id)
            await msg.answer("✅ Спасибо! Заявка отправлена.")
            return

    # GPT-ответ
    try:
        answer = await get_answer(msg.text, user_id=user_id)
        await msg.answer(answer)
    except Exception as e:
        logger.error(f"GPT error: {e}")
        await msg.answer("🤖 Временно не могу ответить.")
