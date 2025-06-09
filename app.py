### app.py
from fastapi import FastAPI
from webhook import api_router
from loguru import logger

app = FastAPI()
app.include_router(api_router)

@app.get("/")
async def root():
    return {"status": "ok"}

@app.on_event("startup")
async def startup():
    logger.info("✅ FastAPI запущено и готово принимать webhook")
