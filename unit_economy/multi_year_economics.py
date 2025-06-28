from typing import List, Dict, Any, Optional

# Комментарии к каждой строке расчёта (расширяемый словарь)
COMMENTS = {
    "shifts_per_year": "Смен в год: Количество сотрудников × рабочих дней.",
    "main_revenue": "Выручка основная: Смен в год × цена смены.",
    "main_cost": "Себестоимость основная: Смен в год × себестоимость смены.",
    "main_profit": "Опер. прибыль основная: Выручка основная – себестоимость основная.",
    "extra_shifts": "Смен в доп. сменах: Кол-во сотрудников на доп. сменах × рабочих дней.",
    "extra_revenue": "Выручка доп. смен: Смен в доп. сменах × цена доп. смены.",
    "extra_cost": "Себестоимость доп. смен: Смен в доп. сменах × себестоимость доп. смены.",
    "extra_profit": "Опер. прибыль доп. смен: Выручка доп. – себестоимость доп.",
    "total_revenue": "Суммарная выручка: Выручка основная + Выручка доп. смен.",
    "total_cost": "Суммарная себестоимость: Себестоимость основная + Себестоимость доп. смен.",
    "operational_profit": "Суммарная опер. прибыль: Опер. прибыль основная + Опер. прибыль доп. смен.",
}

# Тип для одного года
YearParams = Dict[str, Dict[str, Any]]
YearBlock = Dict[str, Any]

def get_param(prev: Optional[float], config: Dict[str, Any]) -> float:
    """
    Выбирает значение параметра: если ручной ввод — берём value, если index — считаем по индексации.
    """
    mode = config.get("mode", "manual")
    if mode == "manual":
        return float(config.get("value", prev or 0))
    elif mode == "index" and prev is not None:
        percent = float(config.get("percent", 0))
        return round(prev * (1 + percent / 100), 2)
    else:
        return float(prev or 0)

def calculate_personnel_economy(count, days, price, cost):
    shifts_per_year = count * days
    main_revenue = shifts_per_year * price
    main_cost = shifts_per_year * cost
    main_profit = main_revenue - main_cost
    return {
        "shifts_per_year": shifts_per_year,
        "main_revenue": main_revenue,
        "main_cost": main_cost,
        "main_profit": main_profit,
    }

def calculate_extra_shift_block(count, days, price, cost):
    extra_shifts = count * days
    main_revenue = extra_shifts * price
    main_cost = extra_shifts * cost
    main_profit = main_revenue - main_cost
    return {
        "extra_shifts": extra_shifts,
        "main_revenue": main_revenue,
        "main_cost": main_cost,
        "main_profit": main_profit,
    }

def calculate_multi_year_economy(years_data: List[Dict[str, Any]]) -> List[YearBlock]:
    """
    Принимает список лет (каждый год — набор параметров c режимами 'manual'/'index'),
    возвращает массив расчетов по каждому году.
    """
    results = []
    prev_params = None
    for year_block in years_data:
        year = year_block["year"]
        # --- Квалифицированные ---
        q_count = get_param(prev_params["q_count"], year_block["params"]["q_count"]) if prev_params else get_param(None, year_block["params"]["q_count"])
        q_price = get_param(prev_params["q_price"], year_block["params"]["q_price"]) if prev_params else get_param(None, year_block["params"]["q_price"])
        q_cost = get_param(prev_params["q_cost"], year_block["params"]["q_cost"]) if prev_params else get_param(None, year_block["params"]["q_cost"])
        q_days = get_param(prev_params["q_days"], year_block["params"]["q_days"]) if prev_params else get_param(None, year_block["params"]["q_days"])
        q_extra_count = get_param(prev_params["q_extra_count"], year_block["params"]["q_extra_count"]) if prev_params else get_param(None, year_block["params"]["q_extra_count"])
        q_extra_days = get_param(prev_params["q_extra_days"], year_block["params"]["q_extra_days"]) if prev_params else get_param(None, year_block["params"]["q_extra_days"])
        q_extra_price = get_param(prev_params["q_extra_price"], year_block["params"]["q_extra_price"]) if prev_params else get_param(None, year_block["params"]["q_extra_price"])
        q_extra_cost = get_param(prev_params["q_extra_cost"], year_block["params"]["q_extra_cost"]) if prev_params else get_param(None, year_block["params"]["q_extra_cost"])
        # --- Неквалифицированные ---
        nq_count = get_param(prev_params["nq_count"], year_block["params"]["nq_count"]) if prev_params else get_param(None, year_block["params"]["nq_count"])
        nq_price = get_param(prev_params["nq_price"], year_block["params"]["nq_price"]) if prev_params else get_param(None, year_block["params"]["nq_price"])
        nq_cost = get_param(prev_params["nq_cost"], year_block["params"]["nq_cost"])
 if prev_params else get_param(None, year_block["params"]["nq_cost"])
        nq_days = get_param(prev_params["nq_days"], year_block["params"]["nq_days"]) if prev_params else get_param(None, year_block["params"]["nq_days"])
        nq_extra_count = get_param(prev_params["nq_extra_count"], year_block["params"]["nq_extra_count"]) if prev_params else get_param(None, year_block["params"]["nq_extra_count"])
        nq_extra_days = get_param(prev_params["nq_extra_days"], year_block["params"]["nq_extra_days"]) if prev_params else get_param(None, year_block["params"]["nq_extra_days"])
        nq_extra_price = get_param(prev_params["nq_extra_price"], year_block["params"]["nq_extra_price"]) if prev_params else get_param(None, year_block["params"]["nq_extra_price"])
        nq_extra_cost = get_param(prev_params["nq_extra_cost"], year_block["params"]["nq_extra_cost"]) if prev_params else get_param(None, year_block["params"]["nq_extra_cost"])

        kval = calculate_personnel_economy(q_count, q_days, q_price, q_cost)
        kval_extra = calculate_extra_shift_block(q_extra_count, q_extra_days, q_extra_price, q_extra_cost)
        nekval = calculate_personnel_economy(nq_count, nq_days, nq_price, nq_cost)
        nekval_extra = calculate_extra_shift_block(nq_extra_count, nq_extra_days, nq_extra_price, nq_extra_cost)

        kval["extra"] = kval_extra
        nekval["extra"] = nekval_extra
        kval["total_revenue"] = kval["main_revenue"] + kval_extra["main_revenue"]
        kval["total_cost"] = kval["main_cost"] + kval_extra["main_cost"]
        kval["operational_profit"] = kval["main_profit"] + kval_extra["main_profit"]
        nekval["total_revenue"] = nekval["main_revenue"] + nekval_extra["main_revenue"]
        nekval["total_cost"] = nekval["main_cost"] + nekval_extra["main_cost"]
        nekval["operational_profit"] = nekval["main_profit"] + nekval_extra["main_profit"]

        summary = {
            "total_revenue": kval["total_revenue"] + nekval["total_revenue"],
            "total_cost": kval["total_cost"] + nekval["total_cost"],
            "operational_profit": kval["operational_profit"] + nekval["operational_profit"]
        }

        results.append({
            "year": year,
            "params": {
                "q_count": q_count, "q_price": q_price, "q_cost": q_cost, "q_days": q_days,
                "q_extra_count": q_extra_count, "q_extra_days": q_extra_days, "q_extra_price": q_extra_price, "q_extra_cost": q_extra_cost,
                "nq_count": nq_count, "nq_price": nq_price, "nq_cost": nq_cost, "nq_days": nq_days,
                "nq_extra_count": nq_extra_count, "nq_extra_days": nq_extra_days, "nq_extra_price": nq_extra_price, "nq_extra_cost": nq_extra_cost
            },
            "kval": kval, "nekval": nekval, "summary": summary
        })
        # Для индексации далее
        prev_params = {
            "q_count": q_count, "q_price": q_price, "q_cost": q_cost, "q_days": q_days,
            "q_extra_count": q_extra_count, "q_extra_days": q_extra_days, "q_extra_price": q_extra_price, "q_extra_cost": q_extra_cost,
            "nq_count": nq_count, "nq_price": nq_price, "nq_cost": nq_cost, "nq_days": nq_days,
            "nq_extra_count": nq_extra_count, "nq_extra_days": nq_extra_days, "nq_extra_price": nq_extra_price, "nq_extra_cost": nq_extra_cost
        }
    return results
