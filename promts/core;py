import os
import re
import random
from datetime import datetime
from openai import AsyncOpenAI
from prompts.data import *

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def contains(text: str, patterns: list[str]) -> bool:
    return any(re.search(re.escape(p), text) for p in patterns)

def detect_persona(text: str) -> str:
    if contains(text, ["я агент", "у меня клиент", "брокер", "работаю с инвестором"]):
        return "agent"
    if contains(text, ["хочу вложить", "ищу для себя", "покупаю", "смотрю для себя"]):
        return "investor"
    return "neutral"

async def get_answer(question: str, user_id: int = None) -> str:
    q = question.lower()
    persona = detect_persona(q)

    # 🔍 Поиск быстрого ответа
    if persona == "agent":
        for keyword, reply in FAQ_AGENT.items():
            if keyword in q:
                return reply
    elif persona == "investor":
        for keyword, reply in FAQ_INVESTOR.items():
            if keyword in q:
                return reply

    if contains(q, ["просто смотрю", "не знаю", "пока нет", "интересуюсь"]):
        return "🧐 Уточните, вы представляете клиента или просто изучаете рынок?"

    style_prompt = STYLE_PROMPT_AGENT if persona == "agent" else STYLE_PROMPT_INVESTOR
    cta = random.choice(CTA_AGENT if persona == "agent" else CTA_INVESTOR)
    followup = random.choice(FOLLOWUP_AGENT if persona == "agent" else FOLLOWUP_INVESTOR)

    file_hint = ""
    for keyword, hint in FILE_HINTS.items():
        if keyword in q:
            file_hint = f"\n📎 {hint}"
            break

    messages = [
        {"role": "system", "content": style_prompt},
        {"role": "user", "content": question}
    ]

    try:
        if user_id:
            with open("logs/questions.log", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {user_id}: {question}\n")
    except:
        pass

    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=messages
        )
        return response.choices[0].message.content.strip() + f"\n\n{cta}{file_hint}\n\n{followup}"
    except Exception:
        return "📍 Объект функционирует. Документы готовы. Уточните, вы представляете клиента?"
