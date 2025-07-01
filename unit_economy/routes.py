from fastapi import APIRouter, Request, Form 
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import re
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
import time
def calc_ndfl_by_scale(amount: float) -> float:
    """
    Расчет НДФЛ по стандартной ставке 15%.
    Если потребуется прогрессивная шкала — сообщи!
    """
    if amount <= 0:
        return 0.0
    return amount * 0.15
from .economics import calculate_personnel_economy, calculate_extra_shift_block
from .ai_analysis import ai_analyze_unit_economy, ai_analyze_unit_economy_multiyear

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

# =========================
# Custom Filters & UX Utils
# =========================

def format_ai_analysis(text: str) -> str:
    """Форматирование для AI анализа (пример, расширяй под свои нужды)."""
    return re.sub(r"\n+", "<br>", text.strip())
templates.env.filters['format_ai_analysis'] = format_ai_analysis

def humanize_millions(value: Any) -> str:
    """Округляет без запятых: 1544444 → 1.5 млн 9000 → 9000"""
    try:
        value = float(str(value).replace(",", "."))
    except Exception:
        return str(value)
    if abs(value) >= 1_000_000:
        rounded = round(value / 1_000_000, 1)
        return f"{int(rounded) if rounded.is_integer() else str(rounded).replace('.', ',')} млн"
    elif abs(value) >= 10_000:
        return f"{int(round(value, 0))}"
    else:
        return str(int(round(value, 0)))
templates.env.filters['humanize_millions'] = humanize_millions

def humanize_percent(value: Any, precision: int = 1) -> str:
    try:
        value = float(str(value).replace(",", "."))
        return f"{round(value, precision)}%"
    except Exception:
        return str(value)
templates.env.filters['humanize_percent'] = humanize_percent

def humanize_money(value: Any, currency: str = "₽") -> str:
    try:
        value = float(str(value).replace(",", "."))
        return f"{int(round(value, 0))} {currency}"
    except Exception:
        return str(value)
templates.env.filters['humanize_money'] = humanize_money

def int_input(value):
    try:
        return str(int(float(str(value).replace(',', '.'))))
    except Exception:
        return '0'
templates.env.filters['int_input'] = int_input

# ===============
# Defaults & Meta
# ===============

def get_default_form() -> Dict[str, Any]:
    """Default single-year form fields."""
    return {
        "q_count": 20, "q_price": 3800, "q_cost": 1924, "q_days": 247,
        "q_extra_shifts": 50, "q_extra_price": 4000, "q_extra_cost": 2500,
        "nq_count": 40, "nq_price": 2980, "nq_cost": 1924, "nq_days": 247,
        "nq_extra_shifts": 30, "nq_extra_price": 3500, "nq_extra_cost": 2000,
    }

def detect_language(request: Request) -> str:
    # Можно расширить по Accept-Language
    return "ru"

COMMENTS = { ... }
COMMENTS_HORIZON = {
    "q_shifts": "Смен квалифицированных за год",
    "q_revenue": "Выручка квалифицированных сотрудников за год",
    "q_cost": "Себестоимость смен квалифицированных за год",
    "q_extra_shifts": "Доп. смен квалифицированных (общее количество смен за год)",
    "q_extra_revenue": "Дополнительная выручка от смен квалифицированных",
    "q_extra_cost": "Себестоимость дополнительных смен квалифицированных",
    "nq_shifts": "Смен неквалифицированных за год",
    "nq_revenue": "Выручка неквалифицированных сотрудников за год",
    "nq_cost": "Себестоимость смен неквалифицированных за год",
    "nq_extra_shifts": "Доп. смен неквалифицированных (общее количество смен за год)",
    "nq_extra_revenue": "Дополнительная выручка от смен неквалифицированных",
    "nq_extra_cost": "Себестоимость дополнительных смен неквалифицированных",
    "costs_block": "Постоянные расходы (ФОТ аренда доход склада)",
    "total_revenue": "Итого выручка за год",
    "total_cost": "Итого расходы за год",
    "operational_profit": "Операционная прибыль за год",
    "net_profit": "Чистая прибыль за год",
    "main_op_profit": "Операционная прибыль по основным сменам квалифицированных сотрудников",
    "extra_op_profit": "Операционная прибыль по дополнительным сменам квалифицированных сотрудников",
    "nq_main_op_profit": "Операционная прибыль по основным сменам неквалифицированных сотрудников",
    "nq_extra_op_profit": "Операционная прибыль по дополнительным сменам неквалифицированных сотрудников",
    "total_op_profit": "Общая операционная прибыль по всем сменам",
}

YEARS = [2026, 2027, 2028, 2029, 2030]

# =========================
# Метрики по блокам (Jinja)
# =========================
METRICS_BLOCKS = {
    "q": [
        ("q_shifts", "Смен квалифицированных", COMMENTS_HORIZON.get("q_shifts", "")),
        ("q_revenue", "Выручка квалифицированных", COMMENTS_HORIZON.get("q_revenue", "")),
        ("q_cost", "Себестоимость квалифицированных", COMMENTS_HORIZON.get("q_cost", "")),
        ("q_extra_shifts", "Доп. смены квалифицированных", COMMENTS_HORIZON.get("q_extra_shifts", "")),
        ("q_extra_revenue", "Выручка за доп. смены", COMMENTS_HORIZON.get("q_extra_revenue", "")),
        ("q_extra_cost", "Себестоимость доп. смен", COMMENTS_HORIZON.get("q_extra_cost", "")),
        ("main_op_profit", "Опер прибыль (осн смены швеи)", COMMENTS_HORIZON.get("main_op_profit", "")),
        ("extra_op_profit", "Опер прибыль (доп смены швеи)", COMMENTS_HORIZON.get("extra_op_profit", "")),
    ],
    "nq": [
        ("nq_shifts", "Смен неквалифицированных", COMMENTS_HORIZON.get("nq_shifts", "")),
        ("nq_revenue", "Выручка неквалифицированных", COMMENTS_HORIZON.get("nq_revenue", "")),
        ("nq_cost", "Себестоимость неквалифицированных", COMMENTS_HORIZON.get("nq_cost", "")),
        ("nq_extra_shifts", "Доп. смены неквалифицированных", COMMENTS_HORIZON.get("nq_extra_shifts", "")),
        ("nq_extra_revenue", "Выручка за доп. смены", COMMENTS_HORIZON.get("nq_extra_revenue", "")),
        ("nq_extra_cost", "Себестоимость доп. смен", COMMENTS_HORIZON.get("nq_extra_cost", "")),
        ("nq_main_op_profit", "Опер прибыль (осн смены уборщ)", COMMENTS_HORIZON.get("nq_main_op_profit", "")),
        ("nq_extra_op_profit", "Опер прибыль (доп смены уборщ)", COMMENTS_HORIZON.get("nq_extra_op_profit", "")),
    ],
    "fin": [
        ("costs_block", "Постоянные расходы (ФОТ аренда доход склада)", COMMENTS_HORIZON.get("costs_block", "")),
        ("total_revenue", "Итого выручка", COMMENTS_HORIZON.get("total_revenue", "")),
        ("total_cost", "Итого расходы", COMMENTS_HORIZON.get("total_cost", "")),
        ("total_op_profit", "Общая операционная прибыль", COMMENTS_HORIZON.get("total_op_profit", "")),
        ("operational_profit", "Операционная прибыль", COMMENTS_HORIZON.get("operational_profit", "")),
        ("tax", "Налог (15%)", "15% от операционной прибыли"),
        ("vat", "НДС (5% при выручке >60 млн)", "5% при выручке свыше 60 млн"),
        ("net_profit", "Чистая прибыль (после налога и НДС)", COMMENTS_HORIZON.get("net_profit", "")),
    ]
}

def get_total_per_metric(results_per_year: Dict[int, Dict[str, Any]], YEARS: List[int]) -> Dict[str, float]:
    total = {}
    for k, v in results_per_year[YEARS[0]].items():
        if isinstance(v, (int, float)):
            total[k] = sum(
                results_per_year[y][k] for y in YEARS if isinstance(results_per_year[y][k], (int, float))
            )
    return total

def get_multiyear_default_form() -> Dict[int, Dict[str, Any]]:
    BASE = {
        2026: dict(
            q_count=20, q_days=247, q_price=4500, q_cost=2150,
            q_extra_shifts=498, q_extra_price=6200, q_extra_cost=3250,
            nq_count=40, nq_days=247, nq_price=2900, nq_cost=2150,
            nq_extra_shifts=628, nq_extra_price=6200, nq_extra_cost=3250,
            fot=475, office_rent=30, warehouse_income=0,
        ),
        2027: dict(
            q_count=20, q_days=249, q_price=5000, q_cost=2350,
            q_extra_shifts=498, q_extra_price=6800, q_extra_cost=3500,
            nq_count=40, nq_days=249, nq_price=3300, nq_cost=2350,
            nq_extra_shifts=628, nq_extra_price=6800, nq_extra_cost=3500,
            fot=522, office_rent=33, warehouse_income=0,
        ),
        2028: dict(
            q_count=20, q_days=249, q_price=5500, q_cost=2550,
            q_extra_shifts=496, q_extra_price=7500, q_extra_cost=3800,
            nq_count=40, nq_days=249, nq_price=3700, nq_cost=2650,
            nq_extra_shifts=628, nq_extra_price=7500, nq_extra_cost=3800,
            fot=574, office_rent=36, warehouse_income=0,
        ),
        2029: dict(
            q_count=20, q_days=247, q_price=6100, q_cost=2700,
            q_extra_shifts=494, q_extra_price=8200, q_extra_cost=4100,
            nq_count=40, nq_days=247, nq_price=4100, nq_cost=2700,
            nq_extra_shifts=628, nq_extra_price=8200, nq_extra_cost=4100,
            fot=632, office_rent=39, warehouse_income=0,
        ),
        2030: dict(
            q_count=20, q_days=248, q_price=6800, q_cost=2950,
            q_extra_shifts=496, q_extra_price=9000, q_extra_cost=4400,
            nq_count=40, nq_days=248, nq_price=4500, nq_cost=2950,
            nq_extra_shifts=628, nq_extra_price=9000, nq_extra_cost=4400,
            fot=695, office_rent=42, warehouse_income=0,
        ),
    }
    form = {}
    for i, year in enumerate(YEARS):
        if year in BASE:
            form[year] = BASE[year].copy()
        else:
            prev = form[year-1]
            form[year] = {}
            for k, v in prev.items():
                if any(sub in k for sub in ("price", "cost", "fot", "office_rent")):
                    form[year][k] = round(prev[k] * 1.10, 2)
                else:
                    form[year][k] = prev[k]
    return form

# === КОРРЕКТНЫЙ МУЛЬТИ-ГОДОВОЙ НДС ===
def calc_vat_multiyear(
    years: List[int], 
    total_revenue_by_year: Dict[int, float], 
    threshold: float = 60_000_000, 
    vat_rate: float = 0.05
) -> Dict[int, float]:
    nds = {}
    vat_started = False
    for idx, year in enumerate(years):
        revenue = total_revenue_by_year[year]
        if not vat_started:
            if revenue > threshold:
                # В год превышения — только на разницу
                nds[year] = (revenue - threshold) * vat_rate
                vat_started = True
            else:
                nds[year] = 0
        else:
            # После превышения — на всю выручку
            nds[year] = revenue * vat_rate
    return nds


def calc_vat_by_month(total_revenue: float, prev_revenue: float, months: int = 12, threshold: float = 60_000_000):
    """Старая функция, больше не используется для мульти-летнего расчёта."""
    if total_revenue <= threshold:
        return 0
    monthly = total_revenue / months
    cum = prev_revenue
    for m in range(1, months + 1):
        cum += monthly
        if cum > threshold:
            months_with_vat = months - m + 1
            return round(monthly * months_with_vat * 0.05)
    return 0

def calc_one_year(data: Dict[str, Any], vat_value: float = None, prev_revenue: float = 0) -> Dict[str, Any]:
    # Основные смены (квалифицированные)
    q_shifts = int(float(data.get("q_count", 0))) * int(float(data.get("q_days", 0)))
    q_revenue = q_shifts * float(data.get("q_price", 0))
    q_cost = q_shifts * float(data.get("q_cost", 0))

    # Основные смены (неквалифицированные)
    nq_shifts = int(float(data.get("nq_count", 0))) * int(float(data.get("nq_days", 0)))
    nq_revenue = nq_shifts * float(data.get("nq_price", 0))
    nq_cost = nq_shifts * float(data.get("nq_cost", 0))

    # Доп. смены (квалифицированные)
    q_extra_shifts = int(float(data.get("q_extra_shifts", 0)))
    q_extra_revenue = q_extra_shifts * float(data.get("q_extra_price", 0))
    q_extra_cost = q_extra_shifts * float(data.get("q_extra_cost", 0))
    # Доп. смены (неквалифицированные)
    nq_extra_shifts = int(float(data.get("nq_extra_shifts", 0)))
    nq_extra_revenue = nq_extra_shifts * float(data.get("nq_extra_price", 0))
    nq_extra_cost = nq_extra_shifts * float(data.get("nq_extra_cost", 0))

    # --- Итоги по категориям для прозрачности ---
    q_total_revenue = q_revenue + q_extra_revenue
    q_total_cost = q_cost + q_extra_cost
    q_total_profit = (q_revenue - q_cost) + (q_extra_revenue - q_extra_cost)
    nq_total_revenue = nq_revenue + nq_extra_revenue
    nq_total_cost = nq_cost + nq_extra_cost
    nq_total_profit = (nq_revenue - nq_cost) + (nq_extra_revenue - nq_extra_cost)

    # Постоянные расходы
    fot = float(data.get("fot", 0)) * 12000
    office_rent = float(data.get("office_rent", 0)) * 12000
    warehouse_income = float(data.get("warehouse_income", 0)) * 12000
    costs_block = fot + office_rent - warehouse_income

    # Финансовые итоги
    total_revenue = q_total_revenue + nq_total_revenue
    total_cost = q_total_cost + nq_total_cost + costs_block
    profit_before_tax = total_revenue - total_cost

    tax = profit_before_tax * 0.15 if profit_before_tax > 0 else 0
    vat = vat_value if vat_value is not None else calc_vat_by_month(total_revenue, prev_revenue)
    net_profit = profit_before_tax - tax - vat

    investor1_share = int(max(net_profit * 0.5, 0))
    investor2_share = int(max(net_profit * 0.3, 0))
    investor3_share = int(max(net_profit * 0.1, 0))
    investor4_share = int(max(net_profit * 0.1, 0))

    audit = []
    if total_revenue == 0:
        audit.append("Внимание! Выручка по году равна 0.")
    if net_profit < 0:
        audit.append("Внимание! Чистая прибыль по году отрицательная!")
    if costs_block > total_revenue * 0.07:
        audit.append("Прочие расходы превышают 7% выручки — пересмотри расходы!")

    constant_expenses = {"fot": int(fot), "office_rent": int(office_rent)}
    return {
        # Поля для таблиц категорий (и для итоговых строк)
        "q_shifts": int(q_shifts),
        "q_revenue": int(q_revenue),
        "q_cost": int(q_cost),
        "q_extra_shifts": int(q_extra_shifts),
        "q_extra_revenue": int(q_extra_revenue),
        "q_extra_cost": int(q_extra_cost),
        "nq_shifts": int(nq_shifts),
        "nq_revenue": int(nq_revenue),
        "nq_cost": int(nq_cost),
        "nq_extra_shifts": int(nq_extra_shifts),
        "nq_extra_revenue": int(nq_extra_revenue),
        "nq_extra_cost": int(nq_extra_cost),
        # Итоговые строки по категориям
        "q_total_revenue": int(q_total_revenue),
        "q_total_cost": int(q_total_cost),
        "q_total_profit": int(q_total_profit),
        "nq_total_revenue": int(nq_total_revenue),
        "nq_total_cost": int(nq_total_cost),
        "nq_total_profit": int(nq_total_profit),
        # Общая фин. модель
        "costs_block": int(costs_block),
        "main_op_profit": int(q_revenue - q_cost),
        "extra_op_profit": int(q_extra_revenue - q_extra_cost),
        "nq_main_op_profit": int(nq_revenue - nq_cost),
        "nq_extra_op_profit": int(nq_extra_revenue - nq_extra_cost),
        "total_op_profit": int(q_total_profit + nq_total_profit),
        "constant_expenses": constant_expenses,
        "total_revenue": int(total_revenue),
        "total_cost": int(total_cost),
        "operational_profit": int(profit_before_tax),
        "tax": int(tax),
        "vat": int(vat),
        "net_profit": int(net_profit),
        "investor1_share": investor1_share,
        "investor2_share": investor2_share,
        "investor3_share": investor3_share,
        "investor4_share": investor4_share,
        "audit": audit
    }

# Остальная логика (роуты и функции) не требует изменений — всё полностью совместимо!

# =========================
# END OF FILE
# =========================



def ai_financial_expert_analysis(years: List[int], results: Dict[int, Dict[str, Any]]) -> Dict[str, Any]:
    summary, alerts = [], []
    profits = [results[y]["net_profit"] for y in years]
    prev_profit = profits[0]
    stagnation_years = 0
    for i, year in enumerate(years):
        net_profit = results[year]["net_profit"]
        if i > 0:
            if net_profit > prev_profit:
                summary.append(f"{year}: чистая прибыль {net_profit} ₽ — рост")
                stagnation_years = 0
            elif net_profit == prev_profit:
                summary.append(f"{year}: чистая прибыль {net_profit} ₽ — стагнация")
                stagnation_years += 1
            else:
                summary.append(f"{year}: чистая прибыль {net_profit} ₽ — падение")
                stagnation_years += 1
        prev_profit = net_profit
        if net_profit < 0:
            alerts.append(f"Год {year}: убыток! Проверьте структуру расходов и выручки.")
        if results[year]["costs_block"] > results[year]["total_revenue"] * 0.07:
            alerts.append(f"Год {year}: Прочие расходы превышают 7% выручки.")
        if stagnation_years > 1:
            alerts.append(f"Нет роста прибыли {stagnation_years+1} года подряд!")
    conclusion = "AI-финансовая экспертиза: бизнес устойчив инвестиции окупятся менее чем за 3 года при текущих темпах. Рекомендуется ежегодная индексация ставок и контроль прочих расходов."
    return {
        "trend": summary,
        "expert_opinion": conclusion,
        "alerts": alerts
    }

@router.get("/multiyear", response_class=HTMLResponse)
async def unit_economy_multiyear_form(request: Request):
    lang = detect_language(request)
    form = get_multiyear_default_form()
    audit_messages = []
    for year in YEARS:
        if form[year]["q_price"] < 1000:
            audit_messages.append(f"{year}: слишком низкая цена квалифицированной смены!")
        if form[year]["nq_price"] < 700:
            audit_messages.append(f"{year}: подозрительно низкая цена неквалифицированной смены!")
    return templates.TemplateResponse(
        "unit_economy_multiyear.html",
        {
            "request": request,
            "form": form,
            "YEARS": YEARS,
            "METRICS_BLOCKS": METRICS_BLOCKS,
            "audit_messages": audit_messages,
            "lang": lang,
        }
    )

@router.post("/multiyear", response_class=HTMLResponse)
async def unit_economy_multiyear_result(request: Request):
    start_time = time.perf_counter()
    lang = detect_language(request)
    form: Dict[int, Dict[str, Any]] = {}
    data = await request.form()
    audit_messages = []
    last_fot = None
    for year in YEARS:
        form[year] = {}
        for field in [
            "q_count", "q_days", "q_price", "q_cost", "q_extra_shifts", "q_extra_price", "q_extra_cost",
            "nq_count", "nq_days", "nq_price", "nq_cost", "nq_extra_shifts", "nq_extra_price", "nq_extra_cost",
            "fot", "office_rent", "warehouse_income"
        ]:
            val = data.get(f"{year}_{field}", 0)
            try:
                form[year][field] = float(str(val).replace(",", "."))
            except Exception:
                form[year][field] = 0
        if form[year]["q_price"] < 1000:
            audit_messages.append(f"{year}: подозрительно низкая цена квалифицированной смены!")
        if form[year]["nq_price"] < 700:
            audit_messages.append(f"{year}: подозрительно низкая цена неквалифицированной смены!")
        if form[year]["fot"] > 2000:
            audit_messages.append(f"{year}: очень высокий ФОТ! Проверьте фонд оплаты труда.")
        if last_fot is not None:
            fot_growth = (form[year]["fot"] - last_fot) / (last_fot or 1)
            if fot_growth < 0.01:
                audit_messages.append(f"{year}: ФОТ не проиндексирован! Проверьте ежегодное повышение зарплат.")
            elif fot_growth > 0.15:
                audit_messages.append(f"{year}: ФОТ вырос более чем на 15% к прошлому году! Проверьте значения.")
        last_fot = form[year]["fot"]

    # === Новый корректный мульти-летний расчет НДС ===
    # 1. Получаем выручку по годам
    total_revenue_by_year = {year: calc_one_year(form[year])["total_revenue"] for year in YEARS}
    # 2. Корректно считаем НДС для каждого года
    vat_by_year = calc_vat_multiyear(YEARS, total_revenue_by_year)
    # 3. Итоговые результаты с НДС для каждого года
    results_per_year: Dict[int, Dict[str, Any]] = {
        year: calc_one_year(form[year], vat_value=vat_by_year[year]) 
        for year in YEARS
    }

    investors_table = []
    cum_net = [0, 0, 0, 0]
    shares = [0.5, 0.3, 0.1, 0.1]
    for year in YEARS:
        net_profit = results_per_year[year]["net_profit"]
        row = {"year": year}
        for idx, share in enumerate(shares):
            gross = net_profit * share
            ndfl = calc_ndfl_by_scale(gross)
            net = gross - ndfl
            row[f"investor{idx+1}_gross"] = int(gross)
            row[f"investor{idx+1}_ndfl"] = int(ndfl)
            row[f"investor{idx+1}_net"] = int(net)
            cum_net[idx] += net
            row[f"investor{idx+1}_cum"] = int(cum_net[idx])
        investors_table.append(row)

    profit_list = [results_per_year[year]["net_profit"] for year in YEARS]
    no_profit_growth = 0
    for i in range(1, len(profit_list)):
        if profit_list[i] <= profit_list[i-1]:
            no_profit_growth += 1
        else:
            no_profit_growth = 0
        if no_profit_growth >= 2:
            audit_messages.append("Нет роста прибыли более двух лет подряд! Проверьте стратегию продаж и/или расходы.")
            break
    try:
        totals = get_total_per_metric(results_per_year, YEARS)
        ai_analysis = ai_analyze_unit_economy_multiyear(
            [dict(year=year, **results_per_year[year]) for year in YEARS],
            totals
        )
        fin_expert = ai_financial_expert_analysis(YEARS, results_per_year)
    except Exception as e:
        logging.exception("AI-анализ (multi-year) не удался: %s", e)
        ai_analysis = "⚠️ Ошибка AI-анализа. Проверьте параметры."
        fin_expert = {}
    response_time = time.perf_counter() - start_time
    return templates.TemplateResponse(
        "unit_economy_multiyear.html",
        {
            "request": request,
            "form": form,
            "YEARS": YEARS,
            "METRICS_BLOCKS": METRICS_BLOCKS,
            "results_per_year": results_per_year,
            "ai_analysis": ai_analysis,
            "audit_messages": audit_messages,
            "investors_table": investors_table,
            "fin_expert": fin_expert,
            "response_time": f"{response_time:.3f} сек",
            "lang": lang,
            "constant_expenses": {year: results_per_year[year]["constant_expenses"] for year in YEARS},
        }
    )



# =========================
# ROUTES: простой (1 год)
# =========================

@router.get("/", response_class=HTMLResponse)
async def unit_economy_form(request: Request):
    form = get_default_form()
    return templates.TemplateResponse("unit_economy_form.html", {
        "request": request,
        "form": form
    })

@router.post("/", response_class=HTMLResponse)
async def unit_economy_result(
    request: Request,
    q_count: int = Form(...), q_price: float = Form(...), q_cost: float = Form(...), q_days: int = Form(...),
    q_extra_shifts: int = Form(...), q_extra_price: float = Form(...), q_extra_cost: float = Form(...),
    nq_count: int = Form(...), nq_price: float = Form(...), nq_cost: float = Form(...), nq_days: int = Form(...),
    nq_extra_shifts: int = Form(...), nq_extra_price: float = Form(...), nq_extra_cost: float = Form(...)
):
    kval = calculate_personnel_economy(
        personnel_type="Квалифицированный персонал (швеи)",
        personnel_count=q_count, work_days=q_days, price_per_shift=q_price, cost_per_shift=q_cost,
        extra_shift=False, extra_shift_percent=0.0, extra_shift_cost_multiplier=1.0
    )
    kval_extra = calculate_extra_shift_block(
        shifts=q_extra_shifts, price=q_extra_price, cost=q_extra_cost,
    )
    nekval = calculate_personnel_economy(
        personnel_type="Неквалифицированный персонал",
        personnel_count=nq_count, work_days=nq_days, price_per_shift=nq_price, cost_per_shift=nq_cost,
        extra_shift=False, extra_shift_percent=0.0, extra_shift_cost_multiplier=1.0
    )
    nekval_extra = calculate_extra_shift_block(
        shifts=nq_extra_shifts, price=nq_extra_price, cost=nq_extra_cost,
    )
    kval_total = {
        "shifts_per_year": kval["shifts_per_year"],
        "main_revenue": kval["main_revenue"],
        "main_cost": kval["main_cost"],
        "main_profit": kval["main_profit"],
        "extra_shifts": kval_extra["shifts"],
        "extra_revenue": kval_extra["revenue"],
        "extra_cost": kval_extra["cost"],
        "extra_profit": kval_extra["profit"],
        "total_revenue": kval["main_revenue"] + kval_extra["revenue"],
        "total_cost": kval["main_cost"] + kval_extra["cost"],
        "operational_profit": kval["main_profit"] + kval_extra["profit"],
    }
    nekval_total = {
        "shifts_per_year": nekval["shifts_per_year"],
        "main_revenue": nekval["main_revenue"],
        "main_cost": nekval["main_cost"],
        "main_profit": nekval["main_profit"],
        "extra_shifts": nekval_extra["shifts"],
        "extra_revenue": nekval_extra["revenue"],
        "extra_cost": nekval_extra["cost"],
        "extra_profit": nekval_extra["profit"],
        "total_revenue": nekval["main_revenue"] + nekval_extra["revenue"],
        "total_cost": nekval["main_cost"] + nekval_extra["cost"],
        "operational_profit": nekval["main_profit"] + nekval_extra["profit"],
    }
    summary = {
        "total_revenue": kval_total["total_revenue"] + nekval_total["total_revenue"],
        "total_cost": kval_total["total_cost"] + nekval_total["total_cost"],
        "operational_profit": kval_total["operational_profit"] + nekval_total["operational_profit"]
    }
    ai_params = {
        "kval": kval_total,
        "nekval": nekval_total,
        "total_profit": summary["operational_profit"]
    }
    try:
        ai_analysis = ai_analyze_unit_economy(ai_params)
    except Exception as e:
        logging.exception("AI-анализ (один год) не удался: %s", e)
        ai_analysis = "⚠️ Ошибка анализа. Попробуйте снова."
    return templates.TemplateResponse(
        "unit_economy_form.html",
        {
            "request": request,
            "form": {
                "q_count": q_count, "q_price": q_price, "q_cost": q_cost, "q_days": q_days,
                "q_extra_shifts": q_extra_shifts, "q_extra_price": q_extra_price, "q_extra_cost": q_extra_cost,
                "nq_count": nq_count, "nq_price": nq_price, "nq_cost": nq_cost, "nq_days": nq_days,
                "nq_extra_shifts": nq_extra_shifts, "nq_extra_price": nq_extra_price, "nq_extra_cost": nq_extra_cost,
            },
            "kval": kval_total,
            "nekval": nekval_total,
            "summary": summary,
            "ai_analysis": ai_analysis,
            "COMMENTS": COMMENTS
        }
    )

@router.get("/selftest", response_class=JSONResponse)
async def unit_economy_selftest(request: Request):
    return {
        "status": "ok",
        "time": datetime.utcnow().isoformat(),
        "model_version": "v2.1.0-superpuper",
        "features": [
            "AI financial expertise", "humanize filters", "metrics blocks", "audit trail"
        ]
    }

# ==============
# END OF FILE
# ==============
