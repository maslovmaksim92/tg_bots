import logging
import time
from openai import OpenAI, OpenAIError

client = OpenAI()
logger = logging.getLogger("unit_economy.ai_analysis")

MAX_ATTEMPTS = 3
DELAY_SECONDS = 2

# ---- АНАЛИЗ ОДИН ГОД ----
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
Доп. смены: {q_extra_count} сотрудников × {q_extra_days} дней, цена {q_extra_price}₽, себестоимость {q_extra_cost}₽
Итого прибыль: {kval_profit}₽

Неквалифицированный персонал:
Количество сотрудников: {nq_count}
Цена смены: {nq_price}₽
Себестоимость смены: {nq_cost}₽
Рабочих дней: {nq_days}
Доп. смены: {nq_extra_count} сотрудников × {nq_extra_days} дней, цена {nq_extra_price}₽, себестоимость {nq_extra_cost}₽
Итого прибыль: {nekval_profit}₽

Суммарная прибыль: {total_profit}₽
"""

def ai_analyze_unit_economy(params: dict) -> str:
    try:
        prompt = ANALYSIS_PROMPT_TEMPLATE.format(
            q_count=params.get('q_count', 0),
            q_price=params.get('q_price', 0),
            q_cost=params.get('q_cost', 0),
            q_days=params.get('q_days', 0),
            q_extra_count=params.get('q_extra_count', 0),
            q_extra_days=params.get('q_extra_days', 0),
            q_extra_price=params.get('q_extra_price', 0),
            q_extra_cost=params.get('q_extra_cost', 0),
            kval_profit=int(params.get('kval_profit', 0)),
            nq_count=params.get('nq_count', 0),
            nq_price=params.get('nq_price', 0),
            nq_cost=params.get('nq_cost', 0),
            nq_days=params.get('nq_days', 0),
            nq_extra_count=params.get('nq_extra_count', 0),
            nq_extra_days=params.get('nq_extra_days', 0),
            nq_extra_price=params.get('nq_extra_price', 0),
            nq_extra_cost=params.get('nq_extra_cost', 0),
            nekval_profit=int(params.get('nekval_profit', 0)),
            total_profit=int(params.get('total_profit', 0))
        )
    except KeyError as e:
        return f"[AI-анализ] Ошибка формирования prompt: отсутствует поле {e}"
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            logger.info(f"[AI-анализ] Попытка #{attempt}... Запрос к GPT-4o")
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

# ---- МУЛЬТИГОДОВОЙ SWOT АНАЛИЗ ----
ANALYSIS_PROMPT_TEMPLATE_MULTIYEAR = """
Проанализируй динамику unit-экономики по годам 2025–2030. Формат ответа: SWOT-анализ, рекомендации, выводы на основе трендов за все годы. Укажи:
- Ключевые изменения в выручке, прибыли, маржинальности по годам
- Главные риски, точки роста, действия по повышению эффективности

Исходные данные по годам (все значения округлены):

{table}

Суммарная выручка: {total_revenue} ₽
Суммарная чистая прибыль: {total_net_profit} ₽
"""

def ai_analyze_unit_economy_multiyear(results: list, summary: dict) -> str:
    table = (
        "| Год | Выручка | Себестоимость | Опер. прибыль | Чистая прибыль | Инв. 1 (50%) | Инв. 2 (30%) | Инв. 3 (10%) | Инв. 4 (10%) |\n"
        "|-----|---------|---------------|---------------|---------------|--------------|--------------|--------------|--------------|\n"
    )
    for row in results:
        table += (
            f"| {row['year']} "
            f"| {int(row['total_revenue'])} "
            f"| {int(row['total_cost'])} "
            f"| {int(row['operational_profit'])} "
            f"| {int(row['net_profit'])} "
            f"| {int(row.get('investor1_share', 0))} "
            f"| {int(row.get('investor2_share', 0))} "
            f"| {int(row.get('investor3_share', 0))} "
            f"| {int(row.get('investor4_share', 0))} |\n"
        )
    prompt = ANALYSIS_PROMPT_TEMPLATE_MULTIYEAR.format(
        table=table,
        total_revenue=int(summary.get("total_revenue", 0)),
        total_net_profit=int(summary.get("net_profit", 0))
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

# ---- ПРОКАЧАННЫЙ ИНВЕСТОРСКИЙ АНАЛИЗ ----
INVESTOR_PROMPT_TEMPLATE = """
Вы — опытный финансовый директор и институциональный инвестор, оцениваете проект для покупки доли в нём.

**Задача:**  
Дайте холодную, взвешенную оценку экономической модели, строго из позиции инвестора.  
- Приведите главные цифры возврата, сроков окупаемости, долей и рисков.  
- Дайте только то, что убедит именно профессионального инвестора.  
- Если есть слабые места, скажите прямо и без смягчения.
- Без рекламы, только суть и выводы: “купил бы/не купил бы и почему”.

Данные по годам (суммы в ₽):

{table}

Суммарная выручка: {total_revenue}  
Суммарная чистая прибыль: {total_net_profit}  
"""

def ai_investor_analysis_multiyear(results: list, summary: dict) -> str:
    table = (
        "| Год | Выручка | Себестоимость | Опер. прибыль | Чистая прибыль | Инв. 1 (50%) | Инв. 2 (30%) | Инв. 3 (10%) | Инв. 4 (10%) |\n"
        "|-----|---------|---------------|---------------|---------------|--------------|--------------|--------------|--------------|\n"
    )
    for row in results:
        table += (
            f"| {row['year']} "
            f"| {int(row['total_revenue'])} "
            f"| {int(row['total_cost'])} "
            f"| {int(row['operational_profit'])} "
            f"| {int(row['net_profit'])} "
            f"| {int(row.get('investor1_share', 0))} "
            f"| {int(row.get('investor2_share', 0))} "
            f"| {int(row.get('investor3_share', 0))} "
            f"| {int(row.get('investor4_share', 0))} |\n"
        )
    prompt = INVESTOR_PROMPT_TEMPLATE.format(
        table=table,
        total_revenue=int(summary.get("total_revenue", 0)),
        total_net_profit=int(summary.get("net_profit", 0))
    )
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            logger.info(f"[AI-инвестор] Попытка #{attempt}... Запрос к GPT-4o")
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,  # максимально cold-факты
                max_tokens=900
            )
            answer = response.choices[0].message.content.strip()
            logger.info("[AI-инвестор] Ответ GPT-4 получен")
            return answer
        except OpenAIError as e:
            logger.error(f"[AI-инвестор] Ошибка GPT-4: {e}")
            last_error = e
            if attempt < MAX_ATTEMPTS:
                logger.info(f"[AI-инвестор] Ретрай через {DELAY_SECONDS} секунд...")
                time.sleep(DELAY_SECONDS * attempt)
    return f"[AI-инвестор] Не удалось получить ответ от GPT-4: {last_error}"
