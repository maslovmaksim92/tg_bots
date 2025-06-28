import logging
import time
from openai import OpenAI, OpenAIError

client = OpenAI()
logger = logging.getLogger("unit_economy.ai_analysis")

MAX_ATTEMPTS = 3
DELAY_SECONDS = 2

ANALYSIS_PROMPT_TEMPLATE = """
Проанализируй юнит-экономику. Дай SWOT-анализ, рекомендации и выдели формулы.

Данные для анализа:
...

Формулы и пояснения к каждому полю:
{comments_block}

Используй пояснения, чтобы лучше раскрыть сильные и слабые стороны, а также предложить точки для оптимизации.
"""

def ai_analyze_unit_economy(params: dict, comments: dict) -> str:
    comments_block = "\n".join(f"{k}: {v}" for k, v in comments.items())
    params = dict(params)
    params["comments_block"] = comments_block
    # ... далее как раньше

    # Заполняем пропущенные поля дефолтами (иначе KeyError)
    safe = {}
    for k in NEEDED_KEYS:
        safe[k] = params.get(k, 0 if 'profit' in k or 'count' in k or 'days' in k else "")
    # Преобразуем доп.смены в строку если они сложные
    if isinstance(safe["q_extra"], dict):
        safe["q_extra"] = ", ".join(f"{kk}: {vv}" for kk, vv in safe["q_extra"].items())
    if isinstance(safe["nq_extra"], dict):
        safe["nq_extra"] = ", ".join(f"{kk}: {vv}" for kk, vv in safe["nq_extra"].items())
    logger.debug(f"[AI-анализ] Итоговые параметры для prompt: {safe}")

    try:
        prompt = ANALYSIS_PROMPT_TEMPLATE.format(**safe)
    except Exception as e:
        logger.error(f"[AI-анализ] Ошибка генерации prompt: {e}")
        return f"[AI-анализ] Форматирование prompt не удалось: {e}"
    logger.info(f"[AI-анализ] Prompt: {prompt[:400]}...")  # для аудита

    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            logger.info(f"[AI-анализ] Попытка #{attempt}... Запрос к GPT-4")
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=700
            )
            answer = response.choices[0].message.content.strip()
            logger.info("[AI-анализ] Ответ GPT-4 получен")
            return answer
        except OpenAIError as e:
            logger.error(f"[AI-анализ] Ошибка GPT-4: {e}")
            last_error = e
            if attempt < MAX_ATTEMPTS:
                logger.info(f"[AI-анализ] Ретрай через {DELAY_SECONDS * attempt} секунд...")
                time.sleep(DELAY_SECONDS * attempt)
    return f"[AI-анализ] Не удалось получить ответ от GPT-4: {last_error}"
