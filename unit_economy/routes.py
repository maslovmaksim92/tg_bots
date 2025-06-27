from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional
from .economics import calculate_personnel_economy
from .ai_analysis import ai_analyze_unit_economy

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

def get_default_form():
    return {
        "q_count": 10,
        "q_price": 3800,
        "q_cost": 1924,
        "q_days": 247,
        "q_extra": True,
        "nq_count": 40,
        "nq_price": 2980,
        "nq_cost": 1924,
        "nq_days": 247,
        "nq_extra": True,
    }

def checkbox_to_bool(val):
    # Если чекбокс не отправлен — False, если value="true" — True
    return str(val).lower() == "true"

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
    q_extra: Optional[str] = Form(None),
    nq_count: int = Form(...),
    nq_price: float = Form(...),
    nq_cost: float = Form(...),
    nq_days: int = Form(...),
    nq_extra: Optional[str] = Form(None),
    ai_analysis: str = Form("")
):
    kval = calculate_personnel_economy(
        personnel_type="Квалифицированный персонал (швеи)",
        personnel_count=q_count,
        work_days=q_days,
        price_per_shift=q_price,
        cost_per_shift=q_cost,
        extra_shift=checkbox_to_bool(q_extra),
        extra_shift_percent=0.5,
        extra_shift_cost_multiplier=1.5
    )
    nekval = calculate_personnel_economy(
        personnel_type="Неквалифицированный персонал",
        personnel_count=nq_count,
        work_days=nq_days,
        price_per_shift=nq_price,
        cost_per_shift=nq_cost,
        extra_shift=checkbox_to_bool(nq_extra),
        extra_shift_percent=0.25,
        extra_shift_cost_multiplier=1.8
    )
    summary = {
        "total_revenue": kval["total_revenue"] + nekval["total_revenue"],
        "total_cost": kval["total_cost"] + nekval["total_cost"],
        "operational_profit": kval["operational_profit"] + nekval["operational_profit"]
    }
    return templates.TemplateResponse(
        "unit_economy_form.html",
        {
            "request": request,
            "form": {
                "q_count": q_count,
                "q_price": q_price,
                "q_cost": q_cost,
                "q_days": q_days,
                "q_extra": checkbox_to_bool(q_extra),
                "nq_count": nq_count,
                "nq_price": nq_price,
                "nq_cost": nq_cost,
                "nq_days": nq_days,
                "nq_extra": checkbox_to_bool(nq_extra),
            },
            "kval": kval,
            "nekval": nekval,
            "summary": summary,
            "ai_analysis": ai_analysis
        }
    )

@router.post("/ai-analyze", response_class=HTMLResponse)
async def ai_analyze(
    request: Request,
    q_count: int = Form(...),
    q_price: float = Form(...),
    q_cost: float = Form(...),
    q_days: int = Form(...),
    q_extra: Optional[str] = Form(None),
    nq_count: int = Form(...),
    nq_price: float = Form(...),
    nq_cost: float = Form(...),
    nq_days: int = Form(...),
    nq_extra: Optional[str] = Form(None)
):
    kval = calculate_personnel_economy(
        personnel_type="Квалифицированный персонал (швеи)",
        personnel_count=q_count,
        work_days=q_days,
        price_per_shift=q_price,
        cost_per_shift=q_cost,
        extra_shift=checkbox_to_bool(q_extra),
        extra_shift_percent=0.5,
        extra_shift_cost_multiplier=1.5
    )
    nekval = calculate_personnel_economy(
        personnel_type="Неквалифицированный персонал",
        personnel_count=nq_count,
        work_days=nq_days,
        price_per_shift=nq_price,
        cost_per_shift=nq_cost,
        extra_shift=checkbox_to_bool(nq_extra),
        extra_shift_percent=0.25,
        extra_shift_cost_multiplier=1.8
    )
    summary = {
        "total_revenue": kval["total_revenue"] + nekval["total_revenue"],
        "total_cost": kval["total_cost"] + nekval["total_cost"],
        "operational_profit": kval["operational_profit"] + nekval["operational_profit"]
    }
    ai_params = {
        "q_count": q_count,
        "q_price": q_price,
        "q_cost": q_cost,
        "q_days": q_days,
        "q_extra": checkbox_to_bool(q_extra),
        "kval_profit": kval["operational_profit"],
        "nq_count": nq_count,
        "nq_price": nq_price,
        "nq_cost": nq_cost,
        "nq_days": nq_days,
        "nq_extra": checkbox_to_bool(nq_extra),
        "nekval_profit": nekval["operational_profit"],
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
                "q_extra": checkbox_to_bool(q_extra),
                "nq_count": nq_count,
                "nq_price": nq_price,
                "nq_cost": nq_cost,
                "nq_days": nq_days,
                "nq_extra": checkbox_to_bool(nq_extra),
            },
            "kval": kval,
            "nekval": nekval,
            "summary": summary,
            "ai_analysis": ai_analysis
        }
    )
