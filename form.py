import os
from aiogram import Router, F, Bot, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from loguru import logger

# === Переменные окружения ===
AGENT_BOT_TOKEN = os.getenv("AGENT_BOT_TOKEN")
TG_CHAT_LEAD = os.getenv("TG_CHAT_LEAD")

if not AGENT_BOT_TOKEN:
    raise EnvironmentError("❌ AGENT_BOT_TOKEN не задан")

if not TG_CHAT_LEAD:
    raise EnvironmentError("❌ TG_CHAT_LEAD не задан")

# === Инициализация ===
router = Router()
bot = Bot(
    token=AGENT_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
ADMIN_CHAT_ID = int(TG_CHAT_LEAD)

# === Состояния формы ===
class Form(StatesGroup):
    name = State()
    phone = State()
    comment = State()

# === Обработчики ===

@router.message(F.text == "📬 Оставить заявку")
async def start_form(msg: Message, state: FSMContext):
    logger.info(f"📝 Старт формы от {msg.from_user.id}")
    await msg.answer("✍️ Как вас зовут?")
    await state.set_state(Form.name)

@router.message(Form.name)
async def form_name(msg: Message, state: FSMContext):
    name = msg.text.strip()
    if not name:
        await msg.answer("⚠️ Имя не может быть пустым. Введите снова.")
        return
    await state.update_data(name=name)
    await msg.answer("📞 Введите ваш номер телефона:")
    await state.set_state(Form.phone)

@router.message(Form.phone)
async def form_phone(msg: Message, state: FSMContext):
    phone = msg.text.strip()
    if not phone or not phone.replace(" ", "").replace("-", "").isdigit():
        await msg.answer("⚠️ Пожалуйста, введите корректный номер телефона.")
        return
    await state.update_data(phone=phone)
    await msg.answer("💬 Комментарий или вопрос (необязательно). Если ничего нет — напишите «-»")
    await state.set_state(Form.comment)

@router.message(Form.comment)
async def form_comment(msg: Message, state: FSMContext):
    await state.update_data(comment=msg.text.strip())
    data = await state.get_data()

    text = (
        f"📥 *Новая заявка от агента*\n\n"
        f"👤 Имя: {data.get('name')}\n"
        f"📱 Телефон: {data.get('phone')}\n"
        f"💬 Комментарий: {data.get('comment')}\n"
        f"🆔 Telegram: [{msg.from_user.full_name}](tg://user?id={msg.from_user.id})"
    )

    try:
        await bot.send_message(ADMIN_CHAT_ID, text)
        logger.info(f"✅ Заявка отправлена от {msg.from_user.id}")
        await msg.answer("✅ Спасибо! Ваша заявка отправлена.")
    except Exception as e:
        logger.error(f"❌ Ошибка отправки заявки: {e}")
        await msg.answer("⚠️ Не удалось отправить заявку. Попробуйте позже.")

    await state.clear()
