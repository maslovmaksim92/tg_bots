from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional
import re
from .economics import calculate_personnel_economy, calculate_extra_shift_block
from .ai_analysis import ai_analyze_unit_economy, ai_analyze_unit_economy_multiyear

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

def format_ai_analysis(text: str) -> str:
    """Красивое форматирование SWOT/рекомендаций: жирные заголовки и списки."""
    if not text:
        return ""
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'(?:^|\n)[\-–] (.+)', r'<li>\1</li>', text)
    text = re.sub(r'((<li>.+?</li>)+)', r'<ul>\1</ul>', text, flags=re.DOTALL)
    text = re.sub(r'\n', r'<br>', text)
    return text

templates.env.filters['format_ai_analysis'] = format_ai_analysis

# ... (single-year блок без изменений, опущен для краткости) ...

# ========================
# МУЛЬТИГОДОВОЙ БЛОК
# ========================

YEARS = [2025, 2026, 2027, 2028, 2029, 2030]
# Новый блок: выводим только ключевые метрики (без total_revenue, total_cost)
SELECTED_METRICS = [
    ("operational_profit", "Операционная прибыль до налогов, ₽"),
    ("net_profit", "Чистая прибыль, ₽"),
    ("investor1_share", "Доля инвестора 1 (50%, после НДФЛ 15%), ₽"),
    ("investor2_share", "Доля инвестора 2 (30%, после НДФЛ 15%), ₽"),
    ("investor3_share", "Доля инвестора 3 (10%, после НДФЛ 15%), ₽"),
    ("investor4_share", "Доля инвестора 4 (10%, после НДФЛ 15%), ₽"),
]

HORIZON_METRICS = [
    ("total_revenue", "Выручка за год, ₽"),
    ("total_cost", "Себестоимость, ₽"),
    ("operational_profit", "Операционная прибыль до налогов, ₽"),
    ("net_profit", "Чистая прибыль, ₽"),
    ("investor1_share", "Доля инвестора 1 (50%, после НДФЛ 15%), ₽"),
    ("investor2_share", "Доля инвестора 2 (30%, после НДФЛ 15%), ₽"),
    ("investor3_share", "Доля инвестора 3 (10%, после НДФЛ 15%), ₽"),
    ("investor4_share", "Доля инвестора 4 (10%, после НДФЛ 15%), ₽"),
]

def get_multiyear_default_form():
    BASE = {
        2025: dict(
            q_count=10, q_days=247, q_price=3800, q_cost=1924,
            q_extra_count=5, q_extra_days=50, q_extra_price=4000, q_extra_cost=2500,
            nq_count=40, nq_days=247, nq_price=2980, nq_cost=1924,
            nq_extra_count=10, nq_extra_days=30, nq_extra_price=3500, nq_extra_cost=2000,
        ),
        2026: dict(
            q_count=10, q_days=247, q_price=4100, q_cost=2100,
            q_extra_count=5, q_extra_days=50, q_extra_price=4200, q_extra_cost=2700,
            nq_count=40, nq_days=247, nq_price=3200, nq_cost=2100,
            nq_extra_count=10, nq_extra_days=30, nq_extra_price=3700, nq_extra_cost=2200,
        ),
    }
    YEARS = [2025, 2026, 2027, 2028, 2029, 2030]
    form = {}
    for i, year in enumerate(YEARS):
        if year in BASE:
            form[year] = BASE[year].copy()
        else:
            prev = form[year-1]
            form[year] = {}
            for k, v in prev.items():
                if any(x in k for x in ("price", "cost")):
                    form[year][k] = round(prev[k] * 1.10)
                else:
                    form[year][k] = prev[k]
    return form

def calc_one_year(data):
    q_shifts = data["q_count"] * data["q_days"]
    q_revenue = q_shifts * data["q_price"]
    q_cost = q_shifts * data["q_cost"]
    q_profit = q_revenue - q_cost

    q_extra_shifts = data["q_extra_count"] * data["q_extra_days"]
    q_extra_revenue = q_extra_shifts * data["q_extra_price"]
    q_extra_cost = q_extra_shifts * data["q_extra_cost"]
    q_extra_profit = q_extra_revenue - q_extra_cost

    nq_shifts = data["nq_count"] * data["nq_days"]
    nq_revenue = nq_shifts * data["nq_price"]
    nq_cost = nq_shifts * data["nq_cost"]
    nq_profit = nq_revenue - nq_cost

    nq_extra_shifts = data["nq_extra_count"] * data["nq_extra_days"]
    nq_extra_revenue = nq_extra_shifts * data["nq_extra_price"]
    nq_extra_cost = nq_extra_shifts * data["nq_extra_cost"]
    nq_extra_profit = nq_extra_revenue - nq_extra_cost

    total_revenue = q_revenue + q_extra_revenue + nq_revenue + nq_extra_revenue
    total_cost = q_cost + q_extra_cost + nq_cost + nq_extra_cost
    operational_profit = q_profit + q_extra_profit + nq_profit + nq_extra_profit
    net_profit = operational_profit

    investor1_share = net_profit * 0.5 * 0.85
    investor2_share = net_profit * 0.3 * 0.85
    investor3_share = net_profit * 0.1 * 0.85
    investor4_share = net_profit * 0.1 * 0.85

    return {
        "total_revenue": total_revenue,
        "total_cost": total_cost,
        "operational_profit": operational_profit,
        "net_profit": net_profit,
        "investor1_share": investor1_share,
        "investor2_share": investor2_share,
        "investor3_share": investor3_share,
        "investor4_share": investor4_share,
    }

@router.get("/multiyear", response_class=HTMLResponse)
async def unit_economy_multiyear_form(request: Request):
    form = get_multiyear_default_form()
    return templates.TemplateResponse(
        "unit_economy_multiyear.html",
        {"request": request, "form": form, "YEARS": YEARS, "HORIZON_METRICS": HORIZON_METRICS}
    )

@router.post("/multiyear", response_class=HTMLResponse)
async def unit_economy_multiyear_result(request: Request):
    form = {}
    data = await request.form()
    for year in YEARS:
        form[year] = {}
        for field in [
            "q_count", "q_days", "q_price", "q_cost", "q_extra_count", "q_extra_days", "q_extra_price", "q_extra_cost",
            "nq_count", "nq_days", "nq_price", "nq_cost", "nq_extra_count", "nq_extra_days", "nq_extra_price", "nq_extra_cost"
        ]:
            form[year][field] = float(data.get(f"{year}_{field}", 0))

    results_per_year = {year: calc_one_year(form[year]) for year in YEARS}

    total_by_metric = {}
    for metric, _ in HORIZON_METRICS:
        total_by_metric[metric] = sum(results_per_year[year][metric] for year in YEARS)

# AI-анализ динамики (оставляем только один вызов!)
ai_analysis = ai_analyze_unit_economy_multiyear(
    [dict(year=year, **results_per_year[year]) for year in YEARS], total_by_metric
)
# Если нужен reasoning — сделай отдельную функцию или промпт!
ai_reasoning = None  # Или вызови ai_analyze_unit_economy_multiyear() с другим prompt внутри новой функции

    )

    return templates.TemplateResponse(
        "unit_economy_multiyear.html",
        {
            "request": request,
            "form": form,
            "YEARS": YEARS,
            "HORIZON_METRICS": HORIZON_METRICS,
            "SELECTED_METRICS": SELECTED_METRICS,
            "results_per_year": results_per_year,
            "total_by_metric": total_by_metric,
            "ai_analysis": ai_analysis,
            "ai_reasoning": ai_reasoning
        }
    )
