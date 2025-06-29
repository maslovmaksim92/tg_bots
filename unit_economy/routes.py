from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
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

def get_default_form():
    return {
        "q_count": 10,
        "q_price": 3800,
        "q_cost": 1924,
        "q_days": 247,
        "q_extra_count": 5,
        "q_extra_price": 4000,
        "q_extra_cost": 2500,
        "q_extra_days": 50,
        "nq_count": 40,
        "nq_price": 2980,
        "nq_cost": 1924,
        "nq_days": 247,
        "nq_extra_count": 10,
        "nq_extra_price": 3500,
        "nq_extra_cost": 2000,
        "nq_extra_days": 30,
    }

COMMENTS = {
    "shifts_per_year": "Смен в год: Количество сотрудников × рабочих дней",
    "main_revenue": "Выручка основная: Смен в год × цена смены",
    "main_cost": "Себестоимость основная: Смен в год × себестоимость смены",
    "main_profit": "Опер. прибыль основная: Выручка основная – себестоимость основной",
    "extra_shifts": "Смен в доп. сменах: Кол-во сотрудников × рабочих дней доп. смены",
    "extra_revenue": "Выручка с доп. смен: Смен в доп. сменах × цена доп. смены",
    "extra_cost": "Себестоимость доп. смен: Смен в доп. сменах × себестоимость доп. смены",
    "extra_profit": "Опер. прибыль доп. смен: Выручка с доп. смен – себестоимость доп. смен",
    "total_revenue": "Суммарная выручка: Выручка основная + Выручка с доп. смен",
    "total_cost": "Суммарная себестоимость: Себестоимость основная + Себестоимость доп. смен",
    "operational_profit": "Суммарная опер. прибыль: Опер. прибыль основная + Опер. прибыль доп. смен",
}

COMMENTS_HORIZON = {
    "q_shifts": "Смены (квалиф.): Кол-во × дней",
    "q_revenue": "Выручка (квалиф.): Смены × цена смены",
    "q_cost": "Себестоимость (квалиф.): Смены × себестоимость",
    "q_extra_shifts": "Смены в доп. сменах (квалиф.): Кол-во × дней",
    "q_extra_revenue": "Выручка (доп. смены, квалиф.): Смены × цена",
    "q_extra_cost": "Себестоимость (доп. смены, квалиф.): Смены × себестоимость",
    "nq_shifts": "Смены (неквалиф.): Кол-во × дней",
    "nq_revenue": "Выручка (неквалиф.): Смены × цена смены",
    "nq_cost": "Себестоимость (неквалиф.): Смены × себестоимость",
    "nq_extra_shifts": "Смены в доп. сменах (неквалиф.): Кол-во × дней",
    "nq_extra_revenue": "Выручка (доп. смены, неквалиф.): Смены × цена",
    "nq_extra_cost": "Себестоимость (доп. смены, неквалиф.): Смены × себестоимость",
    "costs_block": "ФОТ×12 + аренда×12 − доход со склада×12",
    "total_revenue": "Суммарная выручка: все выручки",
    "total_cost": "Суммарная себестоимость: все себестоимости + расходы",
    "operational_profit": "Операционная прибыль: выручка − себестоимость − расходы + доходы",
    "net_profit": "Чистая прибыль: операционная − налоги/инвесторы",
    "investor1_share": "Доля инвестора 1: 50% от чистой прибыли (после НДФЛ 15%)",
    "investor2_share": "Доля инвестора 2: 30% от чистой прибыли (после НДФЛ 15%)",
    "investor3_share": "Доля инвестора 3: 10% от чистой прибыли (после НДФЛ 15%)",
    "investor4_share": "Доля инвестора 4: 10% от чистой прибыли (после НДФЛ 15%)",
}

METRIC_LABELS = [
    ("q_shifts", "Смены (квалиф.)"),
    ("q_revenue", "Выручка (квалиф.)"),
    ("q_cost", "Себестоимость (квалиф.)"),
    ("q_extra_shifts", "Смены в доп. сменах (квалиф.)"),
    ("q_extra_revenue", "Выручка (доп. смены, квалиф.)"),
    ("q_extra_cost", "Себестоимость (доп. смены, квалиф.)"),
    ("nq_shifts", "Смены (неквалиф.)"),
    ("nq_revenue", "Выручка (неквалиф.)"),
    ("nq_cost", "Себестоимость (неквалиф.)"),
    ("nq_extra_shifts", "Смены в доп. сменах (неквалиф.)"),
    ("nq_extra_revenue", "Выручка (доп. смены, неквалиф.)"),
    ("nq_extra_cost", "Себестоимость (доп. смены, неквалиф.)"),
    ("costs_block", "Прочие расходы/доходы"),
    ("total_revenue", "Суммарная выручка"),
    ("total_cost", "Суммарная себестоимость"),
    ("operational_profit", "Операционная прибыль до налогов"),
    ("net_profit", "Чистая прибыль"),
    ("investor1_share", "Доля инвестора 1 (50%)"),
    ("investor2_share", "Доля инвестора 2 (30%)"),
    ("investor3_share", "Доля инвестора 3 (10%)"),
    ("investor4_share", "Доля инвестора 4 (10%)"),
]

METRICS_WITH_COMMENTS = [
    (metric, label, COMMENTS_HORIZON.get(metric, "")) for metric, label in METRIC_LABELS
]

@router.get("/", response_class=HTMLResponse)
async def unit_economy_form(request: Request):
    form = get_default_form()
    return templates.TemplateResponse("unit_economy_form.html", {"request": request, "form": form})

@router.post("/", response_class=HTMLResponse)
async def unit_economy_result(
    request: Request,
    q_count: int = Form(...),
    q_price: float = Form(...),
    q_cost: float = Form(...),
    q_days: int = Form(...),
    q_extra_count: int = Form(...),
    q_extra_price: float = Form(...),
    q_extra_cost: float = Form(...),
    q_extra_days: int = Form(...),
    nq_count: int = Form(...),
    nq_price: float = Form(...),
    nq_cost: float = Form(...),
    nq_days: int = Form(...),
    nq_extra_count: int = Form(...),
    nq_extra_price: float = Form(...),
    nq_extra_cost: float = Form(...),
    nq_extra_days: int = Form(...)
):
    kval = calculate_personnel_economy(
        personnel_type="Квалифицированный персонал (швеи)",
        personnel_count=q_count,
        work_days=q_days,
        price_per_shift=q_price,
        cost_per_shift=q_cost,
        extra_shift=False,
        extra_shift_percent=0.0,
        extra_shift_cost_multiplier=1.0
    )
    kval_extra = calculate_extra_shift_block(
        count=q_extra_count,
        days=q_extra_days,
        price=q_extra_price,
        cost=q_extra_cost,
    )
    nekval = calculate_personnel_economy(
        personnel_type="Неквалифицированный персонал",
        personnel_count=nq_count,
        work_days=nq_days,
        price_per_shift=nq_price,
        cost_per_shift=nq_cost,
        extra_shift=False,
        extra_shift_percent=0.0,
        extra_shift_cost_multiplier=1.0
    )
    nekval_extra = calculate_extra_shift_block(
        count=nq_extra_count,
        days=nq_extra_days,
        price=nq_extra_price,
        cost=nq_extra_cost,
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
    ai_analysis = ai_analyze_unit_economy(ai_params)
    return templates.TemplateResponse(
        "unit_economy_form.html",
        {
            "request": request,
            "form": {
                "q_count": q_count,
                "q_price": q_price,
                "q_cost": q_cost,
                "q_days": q_days,
                "q_extra_count": q_extra_count,
                "q_extra_price": q_extra_price,
                "q_extra_cost": q_extra_cost,
                "q_extra_days": q_extra_days,
                "nq_count": nq_count,
                "nq_price": nq_price,
                "nq_cost": nq_cost,
                "nq_days": nq_days,
                "nq_extra_count": nq_extra_count,
                "nq_extra_price": nq_extra_price,
                "nq_extra_cost": nq_extra_cost,
                "nq_extra_days": nq_extra_days,
            },
            "kval": kval_total,
            "nekval": nekval_total,
            "summary": summary,
            "ai_analysis": ai_analysis,
            "COMMENTS": COMMENTS
        }
    )

# ========================
# МУЛЬТИГОДОВОЙ БЛОК
# ========================

YEARS = [2026, 2027, 2028, 2029, 2030]

def get_multiyear_default_form():
    BASE = {
        2026: dict(
            q_count=10, q_days=247, q_price=3800, q_cost=2000,
            q_extra_count=10, q_extra_days=247, q_extra_price=5700, q_extra_cost=3000,
            nq_count=40, nq_days=247, nq_price=3000, nq_cost=2000,
            nq_extra_count=40, nq_extra_days=620, nq_extra_price=4500, nq_extra_cost=4500,
            fot=500, office_rent=30, warehouse_income=20,
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
                if any(sub in k for sub in ("price", "cost", "fot", "office_rent", "warehouse_income")):
                    form[year][k] = round(prev[k] * 1.10, 2)
                else:
                    form[year][k] = prev[k]
    return form


def calc_one_year(data):
    q_shifts = data["q_count"] * data["q_days"]
    q_revenue = q_shifts * data["q_price"]
    q_cost = q_shifts * data["q_cost"]
    q_extra_shifts = data["q_extra_count"] * data["q_extra_days"]
    q_extra_revenue = q_extra_shifts * data["q_extra_price"]
    q_extra_cost = q_extra_shifts * data["q_extra_cost"]

    nq_shifts = data["nq_count"] * data["nq_days"]
    nq_revenue = nq_shifts * data["nq_price"]
    nq_cost = nq_shifts * data["nq_cost"]
    nq_extra_shifts = data["nq_extra_count"] * data["nq_extra_days"]
    nq_extra_revenue = nq_extra_shifts * data["nq_extra_price"]
    nq_extra_cost = nq_extra_shifts * data["nq_extra_cost"]

    fot = data.get("fot", 0) * 12_000  # тыс. ₽/мес × 12 × 1000
    office_rent = data.get("office_rent", 0) * 12_000
    warehouse_income = data.get("warehouse_income", 0) * 12_000

    costs_block = fot + office_rent - warehouse_income

    total_revenue = q_revenue + q_extra_revenue + nq_revenue + nq_extra_revenue
    total_cost = q_cost + q_extra_cost + nq_cost + nq_extra_cost + costs_block
    operational_profit = total_revenue - total_cost
    net_profit = operational_profit

    investor1_share = net_profit * 0.5 * 0.85
    investor2_share = net_profit * 0.3 * 0.85
    investor3_share = net_profit * 0.1 * 0.85
    investor4_share = net_profit * 0.1 * 0.85

    return {
        "q_shifts": q_shifts,
        "q_revenue": q_revenue,
        "q_cost": q_cost,
        "q_extra_shifts": q_extra_shifts,
        "q_extra_revenue": q_extra_revenue,
        "q_extra_cost": q_extra_cost,
        "nq_shifts": nq_shifts,
        "nq_revenue": nq_revenue,
        "nq_cost": nq_cost,
        "nq_extra_shifts": nq_extra_shifts,
        "nq_extra_revenue": nq_extra_revenue,
        "nq_extra_cost": nq_extra_cost,
        "costs_block": costs_block,
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
        {
            "request": request,
            "form": form,
            "YEARS": YEARS,
            "METRICS_WITH_COMMENTS": METRICS_WITH_COMMENTS,
            "COMMENTS_HORIZON": COMMENTS_HORIZON,
        }
    )

@router.post("/multiyear", response_class=HTMLResponse)
async def unit_economy_multiyear_result(request: Request):
    form = {}
    data = await request.form()
    for year in YEARS:
        form[year] = {}
        for field in [
            "q_count", "q_days", "q_price", "q_cost", "q_extra_count", "q_extra_days", "q_extra_price", "q_extra_cost",
            "nq_count", "nq_days", "nq_price", "nq_cost", "nq_extra_count", "nq_extra_days", "nq_extra_price", "nq_extra_cost",
            "fot", "office_rent", "warehouse_income"
        ]:
            form[year][field] = float(data.get(f"{year}_{field}", 0))

    results_per_year = {year: calc_one_year(form[year]) for year in YEARS}

    total_by_metric = {}
    for metric, _, _ in METRICS_WITH_COMMENTS:
        total_by_metric[metric] = sum(results_per_year[year][metric] for year in YEARS)

    # Формируем структуру для таблицы инвесторов
    investors_table = []
    for year in YEARS:
        ydata = results_per_year[year]
        investors_table.append({
            "year": year,
            "investor1_share": ydata["investor1_share"],
            "investor2_share": ydata["investor2_share"],
            "investor3_share": ydata["investor3_share"],
            "investor4_share": ydata["investor4_share"],
        })

    ai_analysis = ai_analyze_unit_economy_multiyear(
        [dict(year=year, **results_per_year[year]) for year in YEARS], total_by_metric
    )

    return templates.TemplateResponse(
        "unit_economy_multiyear.html",
        {
            "request": request,
            "form": form,
            "YEARS": YEARS,
            "METRICS_WITH_COMMENTS": METRICS_WITH_COMMENTS,
            "results_per_year": results_per_year,
            "total_by_metric": total_by_metric,
            "ai_analysis": ai_analysis,
            "COMMENTS_HORIZON": COMMENTS_HORIZON,
            "investors_table": investors_table,  # <-- вот это обязательно для шаблона
        }
    )
