"""
RevenueLens AI - Revenue Opportunity & Scenario Simulator
Interactive What-If forecasting engine for CMOs, CROs, and marketing executives.
Simulates the impact of budget reallocations, conversion rate enhancements,
lead qualification improvements, and pricing/deal value adjustments on revenue, ROI, and ROAS.
Maintains strict mathematical consistency without double-counting stage gains.
"""

import pandas as pd
import numpy as np


def simulate_marketing_scenario(
    baseline_kpis: dict,
    spend_multiplier: float = 1.0,
    cpl_delta_pct: float = 0.0,
    mql_rate_delta_pct: float = 0.0,
    conversion_rate_delta_pct: float = 0.0,
    deal_value_delta_pct: float = 0.0,
    budget_reallocation_boost: float = 0.0,
) -> dict:
    """
    Compute mathematically consistent scenario projection given managerial levers.

    Parameters:
    - baseline_kpis: dict containing baseline values (spend, leads, customers, revenue, etc.)
    - spend_multiplier: factor to scale total marketing spend (e.g. 1.10 = +10% budget)
    - cpl_delta_pct: percentage change in cost per lead (e.g. -15.0 = 15% cheaper CPL)
    - mql_rate_delta_pct: relative percentage change in qualification efficiency (e.g. +20%)
    - conversion_rate_delta_pct: relative percentage change in lead-to-customer conversion (e.g. +25%)
    - deal_value_delta_pct: percentage change in average deal size / ACV (e.g. +10%)
    - budget_reallocation_boost: additional efficiency boost from shifting budget from low to high ROAS channels (0-15%)
    """
    base_spend = baseline_kpis.get("spend", 100000.0)
    base_leads = baseline_kpis.get("leads", 1000)
    base_customers = baseline_kpis.get("customers", 50)
    base_revenue = baseline_kpis.get("revenue", 500000.0)
    base_cpl = baseline_kpis.get("cpl", base_spend / max(1, base_leads))
    base_conv = baseline_kpis.get("conversion_rate", (base_customers / max(1, base_leads) * 100.0))
    base_deal_value = baseline_kpis.get("avg_deal_value", base_revenue / max(1, base_customers))
    base_roi = baseline_kpis.get("roi", ((base_revenue - base_spend) / max(1, base_spend) * 100.0))
    base_roas = baseline_kpis.get("roas", base_revenue / max(1, base_spend))

    # 1. Projected Spend
    sim_spend = base_spend * spend_multiplier

    # 2. Projected CPL
    # If budget reallocation boost is applied, it improves CPL efficiency
    effective_cpl_factor = (1.0 + (cpl_delta_pct / 100.0)) * (1.0 - (budget_reallocation_boost / 100.0 * 0.5))
    sim_cpl = max(1.0, base_cpl * effective_cpl_factor)

    # 3. Projected Leads generated
    sim_leads = int(sim_spend / sim_cpl) if sim_cpl > 0 else base_leads

    # 4. Projected Lead-to-Customer Conversion Rate
    # Combines qualification efficiency (MQL boost) and sales execution (conversion boost)
    # Scaled multiplicatively to avoid compounding distortions
    qual_factor = 1.0 + (mql_rate_delta_pct / 100.0 * 0.4)  # 40% pass-through from MQL to won
    sales_factor = 1.0 + (conversion_rate_delta_pct / 100.0)
    realloc_factor = 1.0 + (budget_reallocation_boost / 100.0 * 0.5)

    sim_conv_rate = base_conv * qual_factor * sales_factor * realloc_factor
    sim_conv_rate = min(sim_conv_rate, 45.0)  # Realistic ceiling

    # 5. Projected Customers Acquired
    sim_customers = int(np.round(sim_leads * (sim_conv_rate / 100.0)))

    # 6. Projected Deal Value
    sim_deal_value = max(500.0, base_deal_value * (1.0 + (deal_value_delta_pct / 100.0)))

    # 7. Projected Revenue
    sim_revenue = sim_customers * sim_deal_value

    # 8. Projected Unit Economics
    sim_cac = (sim_spend / sim_customers) if sim_customers > 0 else 0.0
    sim_roas = (sim_revenue / sim_spend) if sim_spend > 0 else 0.0
    sim_roi = ((sim_revenue - sim_spend) / sim_spend * 100.0) if sim_spend > 0 else 0.0
    sim_net_profit = sim_revenue - sim_spend
    base_net_profit = base_revenue - base_spend

    comparison_df = pd.DataFrame([
        {
            "Metric": "Total Marketing Spend ($)",
            "Baseline": base_spend,
            "Simulated Scenario": sim_spend,
            "Absolute Delta": sim_spend - base_spend,
            "Percentage Change (%)": ((sim_spend - base_spend) / base_spend * 100.0) if base_spend > 0 else 0.0,
            "Format": "currency"
        },
        {
            "Metric": "Leads Generated",
            "Baseline": base_leads,
            "Simulated Scenario": sim_leads,
            "Absolute Delta": sim_leads - base_leads,
            "Percentage Change (%)": ((sim_leads - base_leads) / base_leads * 100.0) if base_leads > 0 else 0.0,
            "Format": "integer"
        },
        {
            "Metric": "Cost Per Lead (CPL) ($)",
            "Baseline": base_cpl,
            "Simulated Scenario": sim_cpl,
            "Absolute Delta": sim_cpl - base_cpl,
            "Percentage Change (%)": ((sim_cpl - base_cpl) / base_cpl * 100.0) if base_cpl > 0 else 0.0,
            "Format": "currency"
        },
        {
            "Metric": "Lead-to-Customer Conv. Rate (%)",
            "Baseline": base_conv,
            "Simulated Scenario": sim_conv_rate,
            "Absolute Delta": sim_conv_rate - base_conv,
            "Percentage Change (%)": ((sim_conv_rate - base_conv) / base_conv * 100.0) if base_conv > 0 else 0.0,
            "Format": "percent"
        },
        {
            "Metric": "Customers Acquired",
            "Baseline": base_customers,
            "Simulated Scenario": sim_customers,
            "Absolute Delta": sim_customers - base_customers,
            "Percentage Change (%)": ((sim_customers - base_customers) / base_customers * 100.0) if base_customers > 0 else 0.0,
            "Format": "integer"
        },
        {
            "Metric": "Average Deal Value ($)",
            "Baseline": base_deal_value,
            "Simulated Scenario": sim_deal_value,
            "Absolute Delta": sim_deal_value - base_deal_value,
            "Percentage Change (%)": ((sim_deal_value - base_deal_value) / base_deal_value * 100.0) if base_deal_value > 0 else 0.0,
            "Format": "currency"
        },
        {
            "Metric": "Customer Acquisition Cost (CAC) ($)",
            "Baseline": (base_spend / base_customers) if base_customers > 0 else 0.0,
            "Simulated Scenario": sim_cac,
            "Absolute Delta": sim_cac - ((base_spend / base_customers) if base_customers > 0 else 0.0),
            "Percentage Change (%)": ((sim_cac - (base_spend / base_customers)) / (base_spend / base_customers) * 100.0) if base_customers > 0 else 0.0,
            "Format": "currency"
        },
        {
            "Metric": "Attributed Revenue ($)",
            "Baseline": base_revenue,
            "Simulated Scenario": sim_revenue,
            "Absolute Delta": sim_revenue - base_revenue,
            "Percentage Change (%)": ((sim_revenue - base_revenue) / base_revenue * 100.0) if base_revenue > 0 else 0.0,
            "Format": "currency"
        },
        {
            "Metric": "Return on Ad Spend (ROAS)",
            "Baseline": base_roas,
            "Simulated Scenario": sim_roas,
            "Absolute Delta": sim_roas - base_roas,
            "Percentage Change (%)": ((sim_roas - base_roas) / base_roas * 100.0) if base_roas > 0 else 0.0,
            "Format": "multiplier"
        },
        {
            "Metric": "Marketing ROI (%)",
            "Baseline": base_roi,
            "Simulated Scenario": sim_roi,
            "Absolute Delta": sim_roi - base_roi,
            "Percentage Change (%)": ((sim_roi - base_roi) / abs(base_roi) * 100.0) if base_roi != 0 else 0.0,
            "Format": "percent"
        },
        {
            "Metric": "Net Contribution Margin ($)",
            "Baseline": base_net_profit,
            "Simulated Scenario": sim_net_profit,
            "Absolute Delta": sim_net_profit - base_net_profit,
            "Percentage Change (%)": ((sim_net_profit - base_net_profit) / abs(base_net_profit) * 100.0) if base_net_profit != 0 else 0.0,
            "Format": "currency"
        }
    ])

    return {
        "comparison_table": comparison_df,
        "revenue_delta": sim_revenue - base_revenue,
        "revenue_growth_pct": ((sim_revenue - base_revenue) / base_revenue * 100.0) if base_revenue > 0 else 0.0,
        "net_profit_delta": sim_net_profit - base_net_profit,
        "sim_spend": sim_spend,
        "sim_revenue": sim_revenue,
        "sim_roas": sim_roas,
        "sim_roi": sim_roi,
        "sim_customers": sim_customers
    }
