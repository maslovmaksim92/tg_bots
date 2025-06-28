import logging
import time
from openai import OpenAI, OpenAIError

client = OpenAI()
logger = logging.getLogger("unit_economy.ai_analysis")

MAX_ATTEMPTS = 3
DELAY_SECONDS = 2

ANALYSIS_PROMPT_TEMPLATE_MULTIYEAR = """
Проанализируй динамику unit-экономики по годам 2025–2030. Формат ответа: SWOT-анализ, рекомендации, выводы на основе трендов за все годы. Укажи:
- Ключевые изменения в выручке, прибыли, маржинальности по годам
- Главные риски, точки роста, действия по повышению эффективности

Исходные данные по годам (все значения округлены):
{table}

Суммарная выручка: {total_revenue} ₽\nСуммарная чистая прибыль: {total_net_profit} ₽
"""

def ai_analyze_unit_economy_multiyear(results: list, summary: dict) -> str:
    """
    AI-анализ динамики по годам (SWOT и рекомендации по трендам)
    """
    table = "| Год | Выручка | Себестоимость | Опер. прибыль | Чистая прибыль | Доля инвестора |\n"
    table += "|-----|---------|---------------|---------------|---------------|---------------|\n"
    for row in results:
        table += f"| {row['year']} | {int(row['total_revenue'])} | {int(row['total_cost'])} | {int(row['operational_profit'])} | {int(row['net_profit'])} | {int(row['investor_share'])} |\n"
    prompt = ANALYSIS_PROMPT_TEMPLATE_MULTIYEAR.format(
        table=table,
        total_revenue=int(summary["total_revenue"]),
        total_net_profit=int(summary["total_net_profit"])
    )
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            logger.info(f"[AI-мультигод] Попытка #{attempt}... Запрос к GPT-4o")
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=900
            )
            answer = response.choices[0].message.content.strip()
            logger.info("[AI-мультигод] Ответ GPT-4 получен")
            return answer
        except OpenAIError as e:
            logger.error(f"[AI-мультигод] Ошибка GPT-4: {e}")
            last_error = e
            if attempt < MAX_ATTEMPTS:
                logger.info(f"[AI-мультигод] Ретрай через {DELAY_SECONDS} секунд...")
                time.sleep(DELAY_SECONDS * attempt)
    return f"[AI-мультигод] Не удалось получить ответ от GPT-4: {last_error}"  
