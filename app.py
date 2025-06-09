from fastapi import FastAPI
from webhook import api_router  # ранее было: router
from loguru import logger

app = FastAPI()
app.include_router(api_router)

@app.on_event("startup")
async def startup():
    logger.info("✅ FastAPI запущено с webhook (без polling)")
