from typing import Dict

def calculate_personnel_economy(
    personnel_type: str,
    personnel_count: int,
    work_days: int,
    price_per_shift: float,
    cost_per_shift: float,
    extra_shift: bool = False,
    extra_shift_percent: float = 0.5,
    extra_shift_cost_multiplier: float = 1.5
) -> Dict[str, float]:
    """
    Универсальный расчет unit-экономики для персонала.
    Поддержка квалифицированного (швеи) и неквалифицированного (уборка) персонала.
    """
    shifts_per_year = work_days * personnel_count
    total_revenue = price_per_shift * shifts_per_year
    total_cost = cost_per_shift * shifts_per_year
    operational_profit = total_revenue - total_cost

    extra_shift_revenue = 0
    extra_shift_cost = 0
    extra_operational_profit = 0
    extra_shifts = 0
    if extra_shift:
        extra_shifts = int(shifts_per_year * extra_shift_percent)
        extra_shift_revenue = price_per_shift * extra_shifts * (1 + (extra_shift_cost_multiplier - 1))
        extra_shift_cost = cost_per_shift * extra_shifts * extra_shift_cost_multiplier
        extra_operational_profit = extra_shift_revenue - extra_shift_cost

    summary = {
        "personnel_type": personnel_type,
        "personnel_count": personnel_count,
        "work_days": work_days,
        "shifts_per_year": shifts_per_year,
        "main_revenue": total_revenue,
        "main_cost": total_cost,
        "main_profit": operational_profit,
        "extra_shifts": extra_shifts,
        "extra_revenue": extra_shift_revenue,
        "extra_cost": extra_shift_cost,
        "extra_profit": extra_operational_profit,
        "total_revenue": total_revenue + extra_shift_revenue,
        "total_cost": total_cost + extra_shift_cost,
        "operational_profit": operational_profit + extra_operational_profit
    }
    return summary
    
def calculate_extra_shift_block(count, days, price, cost):
    """
    Расчёт блока дополнительных смен:
    - count: количество сотрудников на доп. сменах
    - days: рабочих дней доп. смен
    - price: выручка с 1 доп. смены
    - cost: себестоимость 1 доп. смены
    """
    shifts = count * days
    revenue = shifts * price
    cost_val = shifts * cost
    profit = revenue - cost_val
    return {
        "shifts": shifts,
        "revenue": revenue,
        "cost": cost_val,
        "profit": profit,
    }
