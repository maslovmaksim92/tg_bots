import os
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from fastapi import APIRouter, Request
from loguru import logger

from agent_bot.handler import router as main_router
from agent_bot.form import router as form_router

# === Проверка переменных окружения ===
WEBHOOK_PATH = "/webhook/agent"
WEBHOOK_URL = os.getenv("AGENT_WEBHOOK_URL")
TOKEN = os.getenv("AGENT_BOT_TOKEN")

if not TOKEN:
    raise EnvironmentError("❌ Переменная окружения AGENT_BOT_TOKEN не найдена")
if not WEBHOOK_URL:
    raise EnvironmentError("❌ Переменная AGENT_WEBHOOK_URL не задана")

# === Инициализация бота ===
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(main_router)
dp.include_router(form_router)

# === FastAPI роутер ===
api_router = APIRouter()

@api_router.post(WEBHOOK_PATH)
async def telegram_webhook(request: Request):
    try:
        update = types.Update.model_validate(await request.json())
        await dp.feed_update(bot, update)
        return {"ok": True}
    except Exception as e:
        logger.error(f"❌ Ошибка в webhook обработке: {e}")
        return {"ok": False, "error": str(e)}

@dp.startup()
async def on_startup():
    try:
        await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)
        logger.info(f"✅ Webhook установлен: {WEBHOOK_URL}")
    except Exception as e:
        logger.error(f"❌ Не удалось установить webhook: {e}")
