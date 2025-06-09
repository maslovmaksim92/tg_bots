import os
import random
from pathlib import Path

from aiogram import Bot, Dispatcher, Router, types, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton,
    FSInputFile,
    InputMediaPhoto,
)
from aiogram.types.update import Update
from fastapi import FastAPI, Request
from loguru import logger

from agent_bot.prompts import get_answer

# === Telegram Bot Setup ===
AGENT_BOT_TOKEN = os.getenv("AGENT_BOT_TOKEN")
TG_CHAT_LEAD = os.getenv("TG_CHAT_LEAD")
BASE_WEBHOOK = os.getenv("WEBHOOK_URL")

if not AGENT_BOT_TOKEN:
    raise EnvironmentError("❌ Переменная окружения AGENT_BOT_TOKEN не найдена")

if not TG_CHAT_LEAD:
    raise EnvironmentError("❌ TG_CHAT_LEAD не задан")

if not BASE_WEBHOOK:
    raise EnvironmentError("❌ WEBHOOK_URL не задан")

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = BASE_WEBHOOK + WEBHOOK_PATH

bot = Bot(
    token=AGENT_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
router = Router()
dp = Dispatcher()
dp.include_router(router)

# === FastAPI App ===
app = FastAPI()

# === Клавиатура ===
def get_main_keyboard():
    return ReplyKeyboardMarkup(
        resize_keyboard=True,
        keyboard=[
            [KeyboardButton(text="📁 Получить КП")],
            [KeyboardButton(text="📷 Фото объекта")],
            [KeyboardButton(text="📝 Оставить заявку")],
        ]
    )

user_states = {}

@router.message(F.text.lower() == "/start")
async def start_handler(msg: Message):
    logger.info(f"▶️ /start от {msg.from_user.id}")
    await msg.answer(
        "👋 Добро пожаловать! Я — Telegram-ассистент по продаже уникального коммерческого объекта в Калуге.\n\n"
        "🏢 *Объект*: гостиница (1089 м²), переоборудованная под УФИЦ\n"
        "📍 *Адрес*: Калуга, пер. Сельский, 8а\n"
        "💰 *Цена*: 56 млн ₽ *(возможен торг)*\n"
        "📈 *Доход*: аренда от ООО «Ваш Дом» / УФИЦ (ФСИН)\n"
        "🗓️ *Срок*: аренда 10 лет, triple-net\n"
        "🏛️ *Собственник*: ООО «Ваш Дом»\n\n"
        "Вы можете:\n"
        "📑 Получить КП\n"
        "📷 Посмотреть фото\n"
        "📝 Оставить заявку\n\n"
        "📩 Или просто задайте вопрос — я отвечу!",
        reply_markup=get_main_keyboard()
    )

@router.message(F.text == "📑 Получить КП")
async def send_presentation(msg: Message):
    try:
        logger.info(f"📑 Пользователь {msg.from_user.id} запросил КП")
        docs = sorted(Path("agent_bot/templates").glob("*.pdf"))
        doc_titles = {
            "Presentation GAB Kaluga.pdf": "📊 Коммерческое предложение",
            "egrn.pdf": "📄 Выписка из ЕГРН",
            "resume.pdf": "📋 Резюме объекта",
            "svod_pravil_308.pdf": "📘 Свод правил",
            "tex_plan.pdf": "📐 Технический план",
            "otchet.pdf": "📊 Отчет о рыночной стоимости"
        }

        if not docs:
            await msg.answer("❌ Документы не найдены.")
            return

        await msg.answer("📎 Отправляю все документы по объекту:")
        for doc in docs:
            caption = doc_titles.get(doc.name, f"📄 Документ: {doc.name}")
            await msg.answer_document(FSInputFile(doc), caption=caption)

    except Exception as e:
        logger.error(f"Ошибка при отправке КП: {e}")
        await msg.answer("⚠️ Не удалось отправить документы. Попробуйте позже.")

@router.message(F.text == "📷 Фото объекта")
async def send_photos(msg: Message):
    try:
        logger.info(f"📷 Пользователь {msg.from_user.id} запросил фото")
        folder = "agent_bot/images"
        if not os.path.exists(folder):
            await msg.answer("❌ Папка с фото не найдена.")
            return

        photos = []
        for fname in sorted(os.listdir(folder)):
            if fname.lower().endswith((".jpg", ".jpeg", ".png")):
                photos.append(InputMediaPhoto(media=FSInputFile(os.path.join(folder, fname))))

        if not photos:
            await msg.answer("📂 Фото не найдены.")
            return

        for i in range(0, len(photos), 10):
            await msg.answer_media_group(photos[i:i+10])

    except Exception as e:
        logger.error(f"Ошибка при отправке фото: {e}")
        await msg.answer("⚠️ Ошибка при отправке фото.")

@router.message(F.text == "📝 Оставить заявку")
async def start_application(msg: Message):
    logger.info(f"📝 Пользователь {msg.from_user.id} начал заявку")
    user_states[msg.from_user.id] = {"step": "name"}
    await msg.answer("✍️ Введите ваше *ФИО*:")

@router.message(F.text)
async def process_form_or_question(msg: Message):
    user_id = msg.from_user.id
    state = user_states.get(user_id)

    if state:
        if state["step"] == "name":
            state["name"] = msg.text.strip()
            state["step"] = "phone"
            await msg.answer("📞 Введите ваш *номер телефона*:")
            return
        elif state["step"] == "phone":
            state["phone"] = msg.text.strip()
            text = (
                f"📥 *Новая заявка!*\n\n"
                f"👤 ФИО: {state['name']}\n"
                f"📞 Телефон: {state['phone']}\n"
                f"🆔 Telegram ID: {user_id}\n"
                f"👤 Username: @{msg.from_user.username or 'нет'}"
            )
            try:
                await bot.send_message(chat_id=TG_CHAT_LEAD, text=text)
            except Exception as e:
                logger.error(f"Ошибка при отправке заявки: {e}")
            await msg.answer("✅ Спасибо! Заявка принята. Мы с вами свяжемся.")
            user_states.pop(user_id, None)
            return

    # Вопрос — GPT-ответ
    if msg.text:
        logger.info(f"🧠 Вопрос от {msg.from_user.id}: {msg.text}")
        try:
            answer = await get_answer(msg.text, user_id=user_id)
            await msg.answer(answer)
        except Exception as e:
            logger.error(f"Ошибка GPT: {e}")
            await msg.answer("🤖 Временно не могу ответить. Попробуйте позже.")
    else:
        await msg.answer("⚠️ Пожалуйста, введите текст.")

# === Webhook FastAPI ===
@app.post(WEBHOOK_PATH)
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.model_validate(data)
    await dp.feed_update(bot, update)
    return {"status": "ok"}

@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)
    logger.info(f"✅ Webhook установлен: {WEBHOOK_URL}")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    logger.info("🛑 Webhook удалён")
