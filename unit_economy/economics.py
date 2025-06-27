from typing import Dict

def calculate_unit_economy(
    revenue_per_shift: float,
    cost_per_shift: float,
    personnel_count: int,
    work_days: int = 247,
    extra_shift: bool = False,
    extra_shift_percent: float = 0.5,
    extra_shift_cost_multiplier: float = 1.5
) -> Dict[str, float]:
    """
    Расчёт unit-экономики для швейного производства на год.
    """
    shifts_per_year = work_days * personnel_count
    total_revenue = revenue_per_shift * shifts_per_year
    total_cost = cost_per_shift * shifts_per_year
    operational_profit = total_revenue - total_cost

    extra_shift_revenue = 0
    extra_shift_cost = 0
    extra_operational_profit = 0
    if extra_shift:
        extra_shifts = int(shifts_per_year * extra_shift_percent)
        extra_shift_revenue = revenue_per_shift * extra_shifts
        extra_shift_cost = cost_per_shift * extra_shifts * extra_shift_cost_multiplier
        extra_operational_profit = extra_shift_revenue - extra_shift_cost

    summary = {
        "total_revenue": total_revenue + extra_shift_revenue,
        "total_cost": total_cost + extra_shift_cost,
        "operational_profit": operational_profit + extra_operational_profit,
        "main_revenue": total_revenue,
        "main_cost": total_cost,
        "main_profit": operational_profit,
        "extra_revenue": extra_shift_revenue,
        "extra_cost": extra_shift_cost,
        "extra_profit": extra_operational_profit,
        "shifts_per_year": shifts_per_year,
        "extra_shifts": int(shifts_per_year * extra_shift_percent) if extra_shift else 0
    }
    return summary
