"""
RevenueLens AI - KPI Calculation Engine
Computes executive marketing & revenue KPIs, period-over-period comparisons,
and handles edge cases such as division by zero and missing data.
"""

import pandas as pd
import numpy as np
from datetime import datetime


def filter_data(
    campaigns_df: pd.DataFrame,
    leads_df: pd.DataFrame,
    journey_df: pd.DataFrame,
    sales_df: pd.DataFrame,
    date_range: tuple = None,
    selected_campaigns: list = None,
    selected_channels: list = None,
    selected_industries: list = None,
    selected_objectives: list = None,
) -> tuple:
    """
    Filter datasets consistently across campaigns, leads, journey, and sales.
    """
    c_df = campaigns_df.copy() if campaigns_df is not None else pd.DataFrame()
    l_df = leads_df.copy() if leads_df is not None else pd.DataFrame()
    j_df = journey_df.copy() if journey_df is not None else pd.DataFrame()
    s_df = sales_df.copy() if sales_df is not None else pd.DataFrame()

    # 1. Campaign objective & channel filter on campaigns
    if not c_df.empty:
        if selected_channels:
            c_df = c_df[c_df["channel"].isin(selected_channels)]
        if selected_objectives and "campaign_objective" in c_df.columns:
            c_df = c_df[c_df["campaign_objective"].isin(selected_objectives)]
        if selected_campaigns:
            c_df = c_df[c_df["campaign_id"].isin(selected_campaigns)]

    valid_campaign_ids = set(c_df["campaign_id"].unique()) if not c_df.empty else None

    # 2. Filter Leads
    if not l_df.empty:
        if valid_campaign_ids is not None:
            l_df = l_df[l_df["campaign_id"].isin(valid_campaign_ids)]
        if selected_industries and "industry" in l_df.columns:
            l_df = l_df[l_df["industry"].isin(selected_industries)]
        if selected_channels and "lead_source" in l_df.columns:
            l_df = l_df[l_df["lead_source"].isin(selected_channels)]
        if date_range and "lead_date" in l_df.columns:
            start_d, end_d = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
            l_dates = pd.to_datetime(l_df["lead_date"], errors="coerce")
            l_df = l_df[(l_dates >= start_d) & (l_dates <= end_d)]

    valid_customer_ids = set(l_df["customer_id"].unique()) if not l_df.empty else None

    # 3. Filter Sales
    if not s_df.empty:
        if valid_customer_ids is not None:
            s_df = s_df[s_df["customer_id"].isin(valid_customer_ids)]
        if date_range and "opportunity_date" in s_df.columns:
            start_d, end_d = pd.to_datetime(date_range[0]), pd.to_datetime(date_range[1])
            s_dates = pd.to_datetime(s_df["opportunity_date"], errors="coerce")
            s_df = s_df[(s_dates >= start_d) & (s_dates <= end_d)]

    # 4. Filter Journey
    if not j_df.empty:
        if valid_customer_ids is not None:
            j_df = j_df[j_df["customer_id"].isin(valid_customer_ids)]
        if valid_campaign_ids is not None and "campaign_id" in j_df.columns:
            j_df = j_df[j_df["campaign_id"].isin(valid_campaign_ids)]

    return c_df, l_df, j_df, s_df


def calculate_executive_kpis(
    campaigns_df: pd.DataFrame,
    leads_df: pd.DataFrame,
    sales_df: pd.DataFrame,
) -> dict:
    """
    Calculate high-level executive marketing and revenue KPIs.
    All calculations protect against ZeroDivisionError and NaN.
    """
    # Marketing metrics
    spend = float(campaigns_df["spend"].sum()) if campaigns_df is not None and "spend" in campaigns_df.columns else 0.0
    impressions = int(campaigns_df["impressions"].sum()) if campaigns_df is not None and "impressions" in campaigns_df.columns else 0
    clicks = int(campaigns_df["clicks"].sum()) if campaigns_df is not None and "clicks" in campaigns_df.columns else 0

    ctr = (clicks / impressions * 100.0) if impressions > 0 else 0.0

    # Leads metrics
    leads_count = len(leads_df) if leads_df is not None else 0
    mql_count = 0
    sql_count = 0
    if leads_df is not None and not leads_df.empty and "qualification_status" in leads_df.columns:
        mql_count = int((leads_df["qualification_status"].str.upper() == "MQL").sum())
        sql_count = int((leads_df["qualification_status"].str.upper() == "SQL").sum())

    # Sales metrics
    customers_acquired = 0
    total_revenue = 0.0
    if sales_df is not None and not sales_df.empty:
        won_mask = sales_df["sales_stage"].astype(str).str.lower().str.contains("won")
        customers_acquired = int(won_mask.sum())
        total_revenue = float(sales_df.loc[won_mask, "revenue"].sum())

    # Unit economics & Ratios
    cpl = (spend / leads_count) if leads_count > 0 else 0.0
    cac = (spend / customers_acquired) if customers_acquired > 0 else 0.0
    lead_to_customer_rate = (customers_acquired / leads_count * 100.0) if leads_count > 0 else 0.0
    roas = (total_revenue / spend) if spend > 0 else 0.0
    roi = ((total_revenue - spend) / spend * 100.0) if spend > 0 else 0.0
    revenue_per_lead = (total_revenue / leads_count) if leads_count > 0 else 0.0
    avg_deal_value = (total_revenue / customers_acquired) if customers_acquired > 0 else 0.0

    return {
        "spend": spend,
        "impressions": impressions,
        "clicks": clicks,
        "ctr": ctr,
        "leads": leads_count,
        "mql": mql_count,
        "sql": sql_count,
        "customers": customers_acquired,
        "revenue": total_revenue,
        "cpl": cpl,
        "cac": cac,
        "conversion_rate": lead_to_customer_rate,
        "roas": roas,
        "roi": roi,
        "revenue_per_lead": revenue_per_lead,
        "avg_deal_value": avg_deal_value,
    }


def calculate_period_comparison(
    campaigns_df: pd.DataFrame,
    leads_df: pd.DataFrame,
    sales_df: pd.DataFrame,
) -> dict:
    """
    Split the dataset into two equal chronological halves (prior period vs current period)
    to compute delta changes and percentage growth for KPI cards.
    """
    if leads_df is None or leads_df.empty or "lead_date" not in leads_df.columns:
        curr_kpis = calculate_executive_kpis(campaigns_df, leads_df, sales_df)
        return {k: {"current": v, "prior": 0.0, "delta_pct": 0.0} for k, v in curr_kpis.items()}

    leads_copy = leads_df.copy()
    leads_copy["dt"] = pd.to_datetime(leads_copy["lead_date"], errors="coerce")
    valid_leads = leads_copy.dropna(subset=["dt"])

    if valid_leads.empty:
        curr_kpis = calculate_executive_kpis(campaigns_df, leads_df, sales_df)
        return {k: {"current": v, "prior": 0.0, "delta_pct": 0.0} for k, v in curr_kpis.items()}

    min_date = valid_leads["dt"].min()
    max_date = valid_leads["dt"].max()
    mid_date = min_date + (max_date - min_date) / 2

    # Prior period
    prior_leads = valid_leads[valid_leads["dt"] < mid_date]
    curr_leads = valid_leads[valid_leads["dt"] >= mid_date]

    prior_cust_ids = set(prior_leads["customer_id"])
    curr_cust_ids = set(curr_leads["customer_id"])

    prior_sales = sales_df[sales_df["customer_id"].isin(prior_cust_ids)] if sales_df is not None else pd.DataFrame()
    curr_sales = sales_df[sales_df["customer_id"].isin(curr_cust_ids)] if sales_df is not None else pd.DataFrame()

    # Prorate campaigns spend / clicks proportionally by lead count
    total_leads = len(leads_df)
    prior_lead_ratio = len(prior_leads) / total_leads if total_leads > 0 else 0.5
    curr_lead_ratio = len(curr_leads) / total_leads if total_leads > 0 else 0.5

    prior_camp = campaigns_df.copy() if campaigns_df is not None else pd.DataFrame()
    curr_camp = campaigns_df.copy() if campaigns_df is not None else pd.DataFrame()
    if not prior_camp.empty and "spend" in prior_camp.columns:
        prior_camp["spend"] = prior_camp["spend"] * prior_lead_ratio
        prior_camp["impressions"] = prior_camp["impressions"] * prior_lead_ratio
        prior_camp["clicks"] = prior_camp["clicks"] * prior_lead_ratio
    if not curr_camp.empty and "spend" in curr_camp.columns:
        curr_camp["spend"] = curr_camp["spend"] * curr_lead_ratio
        curr_camp["impressions"] = curr_camp["impressions"] * curr_lead_ratio
        curr_camp["clicks"] = curr_camp["clicks"] * curr_lead_ratio

    prior_kpis = calculate_executive_kpis(prior_camp, prior_leads, prior_sales)
    curr_kpis = calculate_executive_kpis(curr_camp, curr_leads, curr_sales)

    comparison = {}
    for k, curr_val in curr_kpis.items():
        prior_val = prior_kpis.get(k, 0.0)
        if prior_val != 0:
            delta_pct = ((curr_val - prior_val) / abs(prior_val)) * 100.0
        else:
            delta_pct = 100.0 if curr_val > 0 else 0.0
        comparison[k] = {
            "current": curr_val,
            "prior": prior_val,
            "delta_pct": delta_pct,
            "is_positive_good": k in ["revenue", "customers", "leads", "mql", "sql", "roas", "roi", "conversion_rate", "avg_deal_value", "ctr", "revenue_per_lead"]
        }

    return comparison
