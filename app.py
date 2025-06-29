from fastapi import FastAPI
from webhook import api_router, bot, WEBHOOK_URL, WEBHOOK_PATH
from loguru import logger
from unit_economy.routes import router as unit_economy_router
from unit_economy.routes import router as multiyear_router

app = FastAPI()

app.include_router(unit_economy_router, prefix="/unit-economy")
app.include_router(api_router)
app.include_router(multiyear_router, prefix="/unit-economy")

@app.get("/")
async def root():
    return {"status": "ok"}

@app.on_event("startup")
async def startup():
    try:
        webhook_url = WEBHOOK_URL + WEBHOOK_PATH
        await bot.set_webhook(url=webhook_url, drop_pending_updates=True)
        logger.info(f"✓ webhook установлен: {webhook_url}")
    except Exception as e:
        logger.error(f"✘ Ошибка установки webhook: {e}")
    logger.info(f"✓ FastAPI запущено и готово принимать webhook")
