import os
import random
from datetime import datetime
from openai import AsyncOpenAI
from promts.data import (
    FAQ_AGENT, FAQ_INVESTOR, FILE_HINTS,
    CTA_AGENT, CTA_INVESTOR,
    FOLLOWUP_AGENT, FOLLOWUP_INVESTOR,
    STYLE_PROMPT_AGENT, STYLE_PROMPT_INVESTOR
)

client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

AGENT_CUES = ["я агент", "у меня клиент", "работаю с инвестором", "брокер"]
INVESTOR_CUES = ["ищу для себя", "хочу вложить", "смотрю для покупки"]

SUMMARY = (
    "📍 *Калуга, пер. Сельский, 8а*\n"
    "🏢 Объект: гостиница, переоборудованная под исправительный центр (УФИЦ)\n"
    "📐 Площадь: 1089,7 м² + 815 м² земли\n"
    "📄 Арендатор: ООО «Ваш Дом». Помещение передано ФСИН по соглашению безвозмездного пользования\n"
    "💼 Аренда: формат Triple Net (NNN), все расходы на арендаторе\n"
    "📈 Доход: 700 тыс ₽/мес (индексация ежегодно), договор на 10 лет\n"
    "🔒 Обременение будет снято до сделки\n"
    "📊 Документы: ЕГРН, техплан, оценка, СП 308\n"
    "💰 Цена: 56 млн ₽ (обсуждается)"
)

CONTACT_INFO = "\n\n📧 vasdom40@yandex.ru\n📞 +7 (920) 092-45-50"

def detect_persona(text: str) -> str:
    text = text.lower()
    if any(cue in text for cue in AGENT_CUES):
        return "agent"
    if any(cue in text for cue in INVESTOR_CUES):
        return "investor"
    return "neutral"

async def get_answer(question: str, user_id: int = None) -> str:
    q_lower = question.lower()

    # Автоответы
    for kw, answer in {**FAQ_AGENT, **FAQ_INVESTOR}.items():
        if kw in q_lower:
            return answer + CONTACT_INFO

    persona = detect_persona(q_lower)

    if persona == "agent":
        style = STYLE_PROMPT_AGENT
        cta = random.choice(CTA_AGENT)
        followup = random.choice(FOLLOWUP_AGENT)
    elif persona == "investor":
        style = STYLE_PROMPT_INVESTOR
        cta = random.choice(CTA_INVESTOR)
        followup = random.choice(FOLLOWUP_INVESTOR)
    else:
        style = STYLE_PROMPT_AGENT + "\n\n" + STYLE_PROMPT_INVESTOR
        cta = random.choice(CTA_AGENT + CTA_INVESTOR)
        followup = random.choice(FOLLOWUP_AGENT + FOLLOWUP_INVESTOR)

    file_hint = ""
    for key, msg in FILE_HINTS.items():
        if key in q_lower:
            file_hint = f"\n📎 {msg}"
            break

    prompt = f"""{SUMMARY}\n\n{style}\n\nВопрос клиента: "{question}"\n\nОтвет:\n1. ✳️ Уникальный объект с гарантированной эксплуатацией\n2. 📄 {cta}{file_hint}\n3. ❓ {followup}"""

    # Логирование
    if user_id:
        try:
            os.makedirs("logs", exist_ok=True)
            with open("logs/questions.log", "a", encoding="utf-8") as f:
                f.write(f"[{datetime.now()}] {user_id}: {question}\n")
        except Exception:
            pass

    # GPT-запрос
    try:
        response = await client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip() + CONTACT_INFO
    except Exception:
        return "📍 Объект функционирует. Документы готовы. Уточните, вы представляете клиента?"
