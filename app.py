from fastapi import FastAPI
from webhook import api_router
from loguru import logger

app = FastAPI()

# Подключаем API webhook
app.include_router(api_router)

@app.on_event("startup")
async def startup():
    logger.info("✅ FastAPI запущено и готово принимать webhook")
