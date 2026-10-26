"""
Automated unit tests for KPI engine calculations and edge case handling.
"""

import pytest
import pandas as pd
from modules.kpi_engine import calculate_executive_kpis, calculate_period_comparison


def test_kpi_calculations_standard():
    campaigns = pd.DataFrame([
        {"campaign_id": "C1", "spend": 1000.0, "impressions": 10000, "clicks": 500},
        {"campaign_id": "C2", "spend": 2000.0, "impressions": 20000, "clicks": 1000},
    ])
    leads = pd.DataFrame([
        {"lead_id": f"L{i}", "customer_id": f"CU{i}", "qualification_status": "SQL" if i % 2 == 0 else "MQL"}
        for i in range(100)
    ])
    sales = pd.DataFrame([
        {"customer_id": f"CU{i}", "sales_stage": "Closed-Won", "revenue": 1000.0}
        for i in range(10)
    ])

    kpis = calculate_executive_kpis(campaigns, leads, sales)

    assert kpis["spend"] == 3000.0
    assert kpis["impressions"] == 30000
    assert kpis["clicks"] == 1500
    assert kpis["ctr"] == pytest.approx(5.0)
    assert kpis["leads"] == 100
    assert kpis["mql"] == 50
    assert kpis["sql"] == 50
    assert kpis["customers"] == 10
    assert kpis["revenue"] == 10000.0
    assert kpis["cpl"] == pytest.approx(30.0)
    assert kpis["cac"] == pytest.approx(300.0)
    assert kpis["conversion_rate"] == pytest.approx(10.0)
    assert kpis["roas"] == pytest.approx(3.333, abs=0.01)
    assert kpis["roi"] == pytest.approx(233.33, abs=0.1)
    assert kpis["avg_deal_value"] == pytest.approx(1000.0)


def test_kpi_edge_cases_zero_division():
    # Empty dataframes shouldn't raise ZeroDivisionError
    empty_camp = pd.DataFrame(columns=["campaign_id", "spend", "impressions", "clicks"])
    empty_leads = pd.DataFrame(columns=["lead_id", "customer_id", "qualification_status"])
    empty_sales = pd.DataFrame(columns=["customer_id", "sales_stage", "revenue"])

    kpis = calculate_executive_kpis(empty_camp, empty_leads, empty_sales)

    assert kpis["spend"] == 0.0
    assert kpis["leads"] == 0
    assert kpis["cpl"] == 0.0
    assert kpis["cac"] == 0.0
    assert kpis["conversion_rate"] == 0.0
    assert kpis["roas"] == 0.0
    assert kpis["roi"] == 0.0
