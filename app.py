from fastapi import FastAPI
from webhook import api_router
from loguru import logger

app = FastAPI()

# Подключаем маршруты (webhook)
app.include_router(api_router)

# Логируем запуск
@app.on_event("startup")
async def startup():
    logger.info("✅ FastAPI запущено и готово принимать webhook (без polling)")

# По желанию: можно добавить healthcheck
@app.get("/")
def root():
    return {"status": "ok", "message": "Bot webhook service is running"}
