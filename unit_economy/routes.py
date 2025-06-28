from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional
import re
from .economics import calculate_personnel_economy, calculate_extra_shift_block
from .ai_analysis import ai_analyze_unit_economy

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

def format_ai_analysis(text: str) -> str:
    """
    Красивое форматирование SWOT/рекомендаций: жирные заголовки и списки.
    """
    if not text:
        return ""
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'(?:^|\n)[\-–] (.+)', r'<li>\1</li>', text)
    text = re.sub(r'((<li>.+?</li>)+)', r'<ul>\1</ul>', text, flags=re.DOTALL)
    text = re.sub(r'\n', r'<br>', text)
    return text

# Регистрируем фильтр для jinja2
templates.env.filters['format_ai_analysis'] = format_ai_analysis

def get_default_form():
    return {
        "q_count": 10,
        "q_price": 3800,
        "q_cost": 1924,
        "q_days": 247,
        # новые поля для ДОП. СМЕН
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

def checkbox_to_bool(val) -> bool:
    if isinstance(val, bool):
        return val
    if val is None:
        return False
    return str(val).strip().lower() == "true"

# Для каждой строки расчёта — комментарий/описание формулы
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
        extra_shift=False,  # отдельная секция!
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
    # Сводные значения (суммы)
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

# Старый AI-анализ через отдельный endpoint — НЕ удалён (можно скрыть в UI)
@router.post("/ai-analyze", response_class=HTMLResponse)
async def ai_analyze(
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
    # ... логика идентична unit_economy_result (можно вынести в отдельную функцию)
    pass  # для краткости опущено
