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

try:
    TG_CHAT_LEAD = int(TG_CHAT_LEAD)
except ValueError:
    raise ValueError("❌ TG_CHAT_LEAD должен быть целым числом (user_id или -100xxx...)")

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

def get_document_caption(filename: str) -> str:
    name = filename.lower()
    base_caption = (
        "ℹ️ Примечание: данный документ является частью комплекта документации, "
        "связанной с объектом недвижимости по адресу: г. Калуга, пер. Сельский, д. 8А. "
        "Подробнее — в отчёте №008/25 от 16.04.2025 и документации УФИЦ ООО \"Ваш Дом\".\n\n"
    )

    if "otchet" in name:
        return f"📎 [Отчёт об оценке]\n\n{base_caption}"
    elif "svod" in name:
        return f"📎 [Свод правил проектирования СП 308]\n\n{base_caption}"
    elif "plan" in name:
        return f"📎 [Поэтажный план объекта]\n\n{base_caption}"
    elif "egrn" in name:
        return f"📎 [Выписка из ЕГРН]\n\n{base_caption}"
    elif "resume" in name:
        return f"📎 [Резюме объекта / Коммерческое предложение]\n\n{base_caption}"
    else:
        return f"📎 [Документ]\n\n{base_caption}"

@router.message(F.text.lower() == "/start")
async def start_handler(msg: Message):
    logger.info(f"▶️ /start от {msg.from_user.id}")
    
    welcome_text = (
        f"👋 Добро пожаловать, *{msg.from_user.full_name}*!\n\n"
        "Я — *Telegram-ассистент* и готов ответить на любые вопросы по недвижимости в свободной форме.\n\n"
        "📎 Вы можете воспользоваться меню:\n"
        "• *Получить КП* — получить комплект документов\n"
        "• *Фото объекта* — посмотреть внешний и внутренний вид\n"
        "• *Оставить заявку* — если объект заинтересовал\n\n"
        "🧠 Просто напишите мне — и я постараюсь помочь.\n\n"
        "❗️*Просьба писать только при реальной заинтересованности в объекте.*"
    )
    
    await msg.answer(welcome_text, reply_markup=get_main_keyboard(), parse_mode="Markdown")



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
            caption = get_document_caption(doc.name)
            await msg.answer_document(FSInputFile(doc), caption=caption)
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

        media = []
        for f in os.listdir(folder):
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                photo = FSInputFile(os.path.join(folder, f))
                media.append(InputMediaPhoto(media=photo))

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
            try:
                await bot.send_message(
                    TG_CHAT_LEAD,
                    f"📥 Новая заявка:\n\n👤 ФИО: {state['name']}\n📞 Телефон: {phone}"
                )
                await msg.answer("✅ Спасибо! Заявка отправлена.")
            except Exception as e:
                logger.error(f"❌ Ошибка при отправке заявки в TG_CHAT_LEAD: {e}")
                await msg.answer("⚠️ Не удалось отправить заявку. Мы уже разбираемся.")
            finally:
                user_states.pop(user_id, None)
            return

    # GPT-ответ
    try:
        answer = await get_answer(msg.text, user_id=user_id)
        await msg.answer(answer)
    except Exception as e:
        logger.error(f"GPT error: {e}")
        await msg.answer("🤖 Временно не могу ответить.")
