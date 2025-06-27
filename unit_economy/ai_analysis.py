import logging
import time
from openai import OpenAI, OpenAIError

client = OpenAI()
logger = logging.getLogger("unit_economy.ai_analysis")

# Рекомендуется брать ключ из переменных окружения
# Пример: client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_ATTEMPTS = 3
DELAY_SECONDS = 2

ANALYSIS_PROMPT_TEMPLATE = """
Проанализируй результаты юнит-экономики (B2B-аутстаффинг, аренда персонала). Дай SWOT-анализ, рекомендации, укажи потенциальные риски и точки роста. Формат ответа:

- Сильные стороны:
- Слабые стороны:
- Возможности:
- Риски:
- Конкретные рекомендации:

Данные для анализа:

Квалифицированный персонал (швеи):
Количество сотрудников: {q_count}
Цена смены: {q_price}₽
Себестоимость смены: {q_cost}₽
Рабочих дней: {q_days}
Доп. смены: {q_extra}
Итого прибыль: {kval_profit}₽

Неквалифицированный персонал:
Количество сотрудников: {nq_count}
Цена смены: {nq_price}₽
Себестоимость смены: {nq_cost}₽
Рабочих дней: {nq_days}
Доп. смены: {nq_extra}
Итого прибыль: {nekval_profit}₽

Суммарная прибыль: {total_profit}₽
"""

def ai_analyze_unit_economy(params: dict) -> str:
    prompt = ANALYSIS_PROMPT_TEMPLATE.format(**params)
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
                logger.info(f"[AI-анализ] Ретрай через {DELAY_SECONDS} секунд...")
                time.sleep(DELAY_SECONDS * attempt)
    return f"[AI-анализ] Не удалось получить ответ от GPT-4: {last_error}"
