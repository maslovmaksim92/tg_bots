from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from .economics import calculate_unit_economy

router = APIRouter()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

@router.get("/", response_class=HTMLResponse)
async def unit_economy_form(request: Request):
    return templates.TemplateResponse("unit_economy_form.html", {"request": request})

@router.post("/", response_class=HTMLResponse)
async def unit_economy_result(
    request: Request,
    revenue_per_shift: float = Form(...),
    cost_per_shift: float = Form(...),
    personnel_count: int = Form(...),
    work_days: int = Form(247),
    extra_shift: bool = Form(False)
):
    results = calculate_unit_economy(
        revenue_per_shift=revenue_per_shift,
        cost_per_shift=cost_per_shift,
        personnel_count=personnel_count,
        work_days=work_days,
        extra_shift=extra_shift
    )
    return templates.TemplateResponse("unit_economy_form.html", {"request": request, "results": results,
                                                               "form": {
                                                                   "revenue_per_shift": revenue_per_shift,
                                                                   "cost_per_shift": cost_per_shift,
                                                                   "personnel_count": personnel_count,
                                                                   "work_days": work_days,
                                                                   "extra_shift": extra_shift
                                                               }})
