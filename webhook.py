import os
from aiogram import Bot, Dispatcher, Router, types
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from fastapi import APIRouter, Request
from loguru import logger

from handler import router as main_router
from form import router as form_router

# === Переменные окружения ===
WEBHOOK_PATH = "/webhook/agent"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
TOKEN = os.getenv("AGENT_BOT_TOKEN")

if not TOKEN:
    raise EnvironmentError("❌ Переменная окружения AGENT_BOT_TOKEN не найдена")
if not WEBHOOK_URL:
    raise EnvironmentError("❌ Переменная WEBHOOK_URL не задана")

# === Инициализация бота и диспетчера ===
bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(main_router)
dp.include_router(form_router)

# === FastAPI router для webhook ===
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
        webhook_url = WEBHOOK_URL + WEBHOOK_PATH
        await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
        logger.info(f"✅ Webhook установлен: {webhook_url}")
    except Exception as e:
        logger.error(f"❌ Не удалось установить webhook: {e}")
