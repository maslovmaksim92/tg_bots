from fastapi import FastAPI
from webhook import api_router, bot, WEBHOOK_URL, WEBHOOK_PATH
from loguru import logger

app = FastAPI()
app.include_router(api_router)

@app.get("/")
async def root():
    return {"status": "ok"}

@app.on_event("startup")
async def startup():
    try:
        webhook_url = WEBHOOK_URL + WEBHOOK_PATH
        await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
        logger.info(f"✅ Webhook установлен: {webhook_url}")
    except Exception as e:
        logger.error(f"❌ Ошибка установки webhook: {e}")

    logger.info("🚀 FastAPI запущено и готово принимать webhook")
