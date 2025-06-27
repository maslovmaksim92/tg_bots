import pytest
from unit_economy.economics import calculate_unit_economy

def test_calculate_unit_economy_basic():
    result = calculate_unit_economy(
        revenue_per_shift=1000,
        cost_per_shift=600,
        personnel_count=10,
        work_days=250
    )
    assert result["total_revenue"] == 1000 * 10 * 250
    assert result["total_cost"] == 600 * 10 * 250
    assert result["operational_profit"] == (1000 - 600) * 10 * 250
    assert result["extra_shifts"] == 0

def test_calculate_unit_economy_with_extra_shift():
    result = calculate_unit_economy(
        revenue_per_shift=2000,
        cost_per_shift=1200,
        personnel_count=5,
        work_days=200,
        extra_shift=True,
        extra_shift_percent=0.5,
        extra_shift_cost_multiplier=1.5
    )
    base_shifts = 5 * 200
    extra_shifts = int(base_shifts * 0.5)
    assert result["main_revenue"] == 2000 * base_shifts
    assert result["main_cost"] == 1200 * base_shifts
    assert result["extra_shifts"] == extra_shifts
    assert result["extra_revenue"] == 2000 * extra_shifts
    assert result["extra_cost"] == 1200 * extra_shifts * 1.5
    assert result["total_revenue"] == result["main_revenue"] + result["extra_revenue"]
    assert result["total_cost"] == result["main_cost"] + result["extra_cost"]
    assert result["operational_profit"] == pytest.approx(
        (result["main_revenue"] - result["main_cost"]) + (result["extra_revenue"] - result["extra_cost"]) 
    )
