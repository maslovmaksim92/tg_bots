YEARS = [2025, 2026, 2027, 2028, 2029, 2030]

COMMENTS = {
    "q_count": "Количество квалифицированного персонала (швеи) в году.",
    "nq_count": "Количество неквалифицированного персонала (уборщицы) в году.",
    "q_days": "Количество рабочих дней для швей в году.",
    "nq_days": "Количество рабочих дней для уборщиц в году.",
    "q_price": "Цена одной смены для швеи, руб.",
    "nq_price": "Цена одной смены для уборщицы, руб.",
    "q_cost": "Себестоимость смены для швеи, руб.",
    "nq_cost": "Себестоимость смены для уборщицы, руб.",
    "q_extra_count": "Кол-во сотрудников в доп. сменах (швеи)",
    "nq_extra_count": "Кол-во сотрудников в доп. сменах (уборщицы)",
    "q_extra_days": "Кол-во доп. смен (швеи)",
    "nq_extra_days": "Кол-во доп. смен (уборщицы)",
    "q_extra_price": "Цена доп. смены (швеи)",
    "nq_extra_price": "Цена доп. смены (уборщицы)",
    "q_extra_cost": "Себестоимость доп. смены (швеи)",
    "nq_extra_cost": "Себестоимость доп. смены (уборщицы)",
    "main_revenue": "Годовая выручка — все смены × цену.",
    "main_cost": "Годовая себестоимость — все смены × себестоимость.",
    "main_profit": "Опер. прибыль по основным сменам: выручка – себестоимость.",
    "extra_revenue": "Годовая выручка по доп. сменам.",
    "extra_cost": "Годовая себестоимость по доп. сменам.",
    "extra_profit": "Опер. прибыль по доп. сменам.",
    "total_revenue": "Итоговая выручка (основные + доп.смены, все сотрудники)",
    "total_cost": "Итоговая себестоимость (основные + доп.смены)",
    "operational_profit": "Суммарная операционная прибыль за год",
    "tax_vat": "НДС 5% от выручки",
    "tax_profit": "Налог на прибыль (УСН 15%) от прибыли до налогообложения",
    "net_profit": "Чистая прибыль после налогов",
    "investor_share": "50% чистой прибыли — доля инвестора"
}

def calculate_unit_economy_2025_2030(input_data):
    """
    input_data: {
        2025: {q_count, q_days, q_price, q_cost, ..., любые параметры},
        2026: {...}, ...
    }
    Возвращает массив dict по годам для дальнейшего рендера/UI/аналитики.
    """
    results = []
    for year in YEARS:
        params = input_data.get(year, {})
        q_count = params.get("q_count", 0)
        q_days = params.get("q_days", 0)
        q_price = params.get("q_price", 0)
        q_cost = params.get("q_cost", 0)
        q_extra_count = params.get("q_extra_count", 0)
        q_extra_days = params.get("q_extra_days", 0)
        q_extra_price = params.get("q_extra_price", 0)
        q_extra_cost = params.get("q_extra_cost", 0)
        nq_count = params.get("nq_count", 0)
        nq_days = params.get("nq_days", 0)
        nq_price = params.get("nq_price", 0)
        nq_cost = params.get("nq_cost", 0)
        nq_extra_count = params.get("nq_extra_count", 0)
        nq_extra_days = params.get("nq_extra_days", 0)
        nq_extra_price = params.get("nq_extra_price", 0)
        nq_extra_cost = params.get("nq_extra_cost", 0)

        # Основные смены (швеи/уборщицы)
        kval_shifts = q_count * q_days
        kval_revenue = kval_shifts * q_price
        kval_cost = kval_shifts * q_cost
        kval_profit = kval_revenue - kval_cost
        # Доп. смены швеи
        kval_extra_shifts = q_extra_count * q_extra_days
        kval_extra_revenue = kval_extra_shifts * q_extra_price
        kval_extra_cost = kval_extra_shifts * q_extra_cost
        kval_extra_profit = kval_extra_revenue - kval_extra_cost
        # Основные смены уборщицы
        nekval_shifts = nq_count * nq_days
        nekval_revenue = nekval_shifts * nq_price
        nekval_cost = nekval_shifts * nq_cost
        nekval_profit = nekval_revenue - nekval_cost
        # Доп. смены уборщицы
        nekval_extra_shifts = nq_extra_count * nq_extra_days
        nekval_extra_revenue = nekval_extra_shifts * nq_extra_price
        nekval_extra_cost = nekval_extra_shifts * nq_extra_cost
        nekval_extra_profit = nekval_extra_revenue - nekval_extra_cost
        # Итоговые суммы по годам
        total_revenue = kval_revenue + kval_extra_revenue + nekval_revenue + nekval_extra_revenue
        total_cost = kval_cost + kval_extra_cost + nekval_cost + nekval_extra_cost
        operational_profit = kval_profit + kval_extra_profit + nekval_profit + nekval_extra_profit
        # Налоги и доли
        tax_vat = round(total_revenue * 0.05, 2)
        profit_before_tax = operational_profit
        tax_profit = round(profit_before_tax * 0.15, 2)
        net_profit = operational_profit - tax_profit
        investor_share = round(net_profit * 0.5, 2)

        results.append({
            "year": year,
            # Параметры
            "q_count": q_count, "q_days": q_days, "q_price": q_price, "q_cost": q_cost,
            "q_extra_count": q_extra_count, "q_extra_days": q_extra_days, "q_extra_price": q_extra_price, "q_extra_cost": q_extra_cost,
            "nq_count": nq_count, "nq_days": nq_days, "nq_price": nq_price, "nq_cost": nq_cost,
            "nq_extra_count": nq_extra_count, "nq_extra_days": nq_extra_days, "nq_extra_price": nq_extra_price, "nq_extra_cost": nq_extra_cost,
            # Расчёты по блокам
            "main_revenue": kval_revenue + nekval_revenue,
            "main_cost": kval_cost + nekval_cost,
            "main_profit": kval_profit + nekval_profit,
            "extra_revenue": kval_extra_revenue + nekval_extra_revenue,
            "extra_cost": kval_extra_cost + nekval_extra_cost,
            "extra_profit": kval_extra_profit + nekval_extra_profit,
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "operational_profit": operational_profit,
            "tax_vat": tax_vat,
            "tax_profit": tax_profit,
            "net_profit": net_profit,
            "investor_share": investor_share
        })
    return results
