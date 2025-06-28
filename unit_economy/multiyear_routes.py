from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from .unit_economy_2025_2030 import calculate_unit_economy_2025_2030, COMMENTS
from .ai_analysis import ai_analyze_unit_economy_multiyear

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

YEARS = [2025, 2026, 2027, 2028, 2029, 2030]

# Для мультигодовой формы — поля ввода по годам
FIELDS = [
    "q_count", "q_days", "q_price", "q_cost", "q_extra_count", "q_extra_days", "q_extra_price", "q_extra_cost",
    "nq_count", "nq_days", "nq_price", "nq_cost", "nq_extra_count", "nq_extra_days", "nq_extra_price", "nq_extra_cost",
]

def get_default_form():
    return {
        year: {
            "q_count": 10 if year == 2025 else 20,
            "q_days": 247,
            "q_price": 3800 + (year-2025)*700,
            "q_cost": 1924 + (year-2025)*200,
            "q_extra_count": 5,
            "q_extra_days": 50,
            "q_extra_price": 4000 + (year-2025)*500,
            "q_extra_cost": 2500 + (year-2025)*200,
            "nq_count": 40,
            "nq_days": 247,
            "nq_price": 2980 + (year-2025)*400,
            "nq_cost": 1924 + (year-2025)*200,
            "nq_extra_count": 10,
            "nq_extra_days": 30,
            "nq_extra_price": 3500 + (year-2025)*400,
            "nq_extra_cost": 2000 + (year-2025)*200,
        }
        for year in YEARS
    }

@router.get("/multiyear", response_class=HTMLResponse)
async def unit_economy_multiyear_form(request: Request):
    form = get_default_form()
    return templates.TemplateResponse(
        "unit_economy_multiyear.html",
        {"request": request, "form": form, "COMMENTS": COMMENTS, "YEARS": YEARS}
    )

@router.post("/multiyear", response_class=HTMLResponse)
async def unit_economy_multiyear_result(request: Request):
    form = {}
    form_data = await request.form()
    for year in YEARS:
        form[year] = {}
        for field in FIELDS:
            val = form_data.get(f"{year}_{field}")
            try:
                form[year][field] = float(val) if val is not None and val != '' else 0.0
            except Exception:
                form[year][field] = 0.0

    results = calculate_unit_economy_2025_2030(form)

    summary = {
        "total_revenue": sum(r["total_revenue"] for r in results),
        "total_cost": sum(r["total_cost"] for r in results),
        "total_operational_profit": sum(r["operational_profit"] for r in results),
        "total_net_profit": sum(r["net_profit"] for r in results)
    }

    # AI-анализ динамики и трендов (только сводка по годам и метрикам)
    ai_analysis = ai_analyze_unit_economy_multiyear(results, summary)

    return templates.TemplateResponse(
        "unit_economy_multiyear.html",
        {
            "request": request,
            "form": form,
            "results": results,
            "summary": summary,
            "COMMENTS": COMMENTS,
            "YEARS": YEARS,
            "ai_analysis": ai_analysis
        }
    )
