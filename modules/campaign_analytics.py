"""
RevenueLens AI - Campaign Performance Analytics
Evaluates campaign and channel efficiency, identifies underperforming vs superstar campaigns,
calculates unit economics (CTR, CPL, CAC, ROAS, ROI), and categorizes campaigns into
strategic marketing quadrants (e.g., Vanity Traps vs Hidden Gems).
"""

import pandas as pd
import numpy as np


def compute_campaign_metrics(
    campaigns_df: pd.DataFrame,
    leads_df: pd.DataFrame,
    sales_df: pd.DataFrame,
    attribution_df: pd.DataFrame = None,
) -> pd.DataFrame:
    """
    Produce a consolidated, multi-metric campaign performance table.
    """
    if campaigns_df is None or campaigns_df.empty:
        return pd.DataFrame()

    c_df = campaigns_df.copy()

    # Calculate Leads per campaign
    if leads_df is not None and not leads_df.empty and "campaign_id" in leads_df.columns:
        leads_summary = leads_df.groupby("campaign_id").agg(
            leads_count=("lead_id", "count"),
            avg_lead_score=("lead_score", "mean") if "lead_score" in leads_df.columns else ("lead_id", "count"),
            avg_followup_time=("follow_up_time_hours", "mean") if "follow_up_time_hours" in leads_df.columns else ("lead_id", "count"),
        ).reset_index()
    else:
        leads_summary = pd.DataFrame(columns=["campaign_id", "leads_count", "avg_lead_score", "avg_followup_time"])

    # Calculate Sales Won per campaign
    if sales_df is not None and not sales_df.empty and leads_df is not None:
        merged_sales = sales_df.merge(leads_df[["customer_id", "campaign_id"]], on="customer_id", how="inner")
        won_sales = merged_sales[merged_sales["sales_stage"].astype(str).str.lower().str.contains("won")]

        sales_summary = won_sales.groupby("campaign_id").agg(
            customers_acquired=("customer_id", "nunique"),
            direct_revenue=("revenue", "sum")
        ).reset_index()
    else:
        sales_summary = pd.DataFrame(columns=["campaign_id", "customers_acquired", "direct_revenue"])

    # Merge everything into campaign dataframe
    merged = c_df.merge(leads_summary, on="campaign_id", how="left")
    merged = merged.merge(sales_summary, on="campaign_id", how="left")

    # If multi-touch attribution table is available, attach attributed revenue
    if attribution_df is not None and not attribution_df.empty and "attributed_revenue" in attribution_df.columns:
        merged = merged.merge(attribution_df[["campaign_id", "attributed_revenue"]], on="campaign_id", how="left")
    else:
        merged["attributed_revenue"] = merged["direct_revenue"]

    # Fill NaNs
    merged["leads_count"] = merged["leads_count"].fillna(0).astype(int)
    merged["customers_acquired"] = merged["customers_acquired"].fillna(0).astype(int)
    merged["direct_revenue"] = merged["direct_revenue"].fillna(0.0)
    merged["attributed_revenue"] = merged["attributed_revenue"].fillna(0.0)
    merged["avg_lead_score"] = merged["avg_lead_score"].fillna(0.0).round(1)
    merged["avg_followup_time"] = merged["avg_followup_time"].fillna(0.0).round(1)

    # Calculate derived KPIs
    merged["ctr_pct"] = np.where(merged["impressions"] > 0, (merged["clicks"] / merged["impressions"] * 100.0).round(2), 0.0)
    merged["lead_conv_rate_pct"] = np.where(merged["clicks"] > 0, (merged["leads_count"] / merged["clicks"] * 100.0).round(2), 0.0)
    merged["lead_to_customer_pct"] = np.where(merged["leads_count"] > 0, (merged["customers_acquired"] / merged["leads_count"] * 100.0).round(2), 0.0)
    merged["cpl"] = np.where(merged["leads_count"] > 0, (merged["spend"] / merged["leads_count"]).round(2), 0.0)
    merged["cac"] = np.where(merged["customers_acquired"] > 0, (merged["spend"] / merged["customers_acquired"]).round(2), 0.0)
    merged["roas"] = np.where(merged["spend"] > 0, (merged["attributed_revenue"] / merged["spend"]).round(2), 0.0)
    merged["roi_pct"] = np.where(merged["spend"] > 0, ((merged["attributed_revenue"] - merged["spend"]) / merged["spend"] * 100.0).round(2), 0.0)

    # Classify into strategic performance quadrants
    # Median thresholds
    med_leads = merged["leads_count"].median()
    med_conv = merged["lead_to_customer_pct"].median()
    med_roas = merged["roas"].median()

    def classify_campaign(row):
        is_high_lead = row["leads_count"] >= med_leads
        is_high_conv = row["lead_to_customer_pct"] >= med_conv
        is_high_roas = row["roas"] >= max(1.5, med_roas)

        if is_high_lead and not is_high_conv:
            return "Vanity Trap (High Volume, Low Quality)"
        elif not is_high_lead and is_high_conv and is_high_roas:
            return "Hidden Gem (High Intent, High ROI)"
        elif row["roi_pct"] < -20.0:
            return "Money Pit (High Spend, Negative ROI)"
        elif is_high_lead and is_high_conv and is_high_roas:
            return "Scale Candidate (Top Performer)"
        else:
            return "Moderate Performer"

    merged["strategic_segment"] = merged.apply(classify_campaign, axis=1)

    return merged.sort_values(by="spend", ascending=False).reset_index(drop=True)


def compute_monthly_trends(
    leads_df: pd.DataFrame,
    sales_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Compute monthly trends of leads generated and closed revenue.
    """
    trend_rows = {}

    if leads_df is not None and not leads_df.empty and "lead_date" in leads_df.columns:
        l_df = leads_df.copy()
        l_df["month"] = pd.to_datetime(l_df["lead_date"], errors="coerce").dt.to_period("M").astype(str)
        l_month = l_df.groupby("month").size().to_dict()
        for m, cnt in l_month.items():
            if m not in trend_rows:
                trend_rows[m] = {"month": m, "leads": 0, "revenue": 0.0, "customers": 0}
            trend_rows[m]["leads"] = cnt

    if sales_df is not None and not sales_df.empty and "opportunity_date" in sales_df.columns:
        s_df = sales_df.copy()
        s_df["month"] = pd.to_datetime(s_df["opportunity_date"], errors="coerce").dt.to_period("M").astype(str)
        won_mask = s_df["sales_stage"].astype(str).str.lower().str.contains("won")

        rev_month = s_df[won_mask].groupby("month")["revenue"].sum().to_dict()
        cust_month = s_df[won_mask].groupby("month")["customer_id"].nunique().to_dict()

        for m, rev in rev_month.items():
            if m not in trend_rows:
                trend_rows[m] = {"month": m, "leads": 0, "revenue": 0.0, "customers": 0}
            trend_rows[m]["revenue"] = round(rev, 2)

        for m, cust in cust_month.items():
            if m not in trend_rows:
                trend_rows[m] = {"month": m, "leads": 0, "revenue": 0.0, "customers": 0}
            trend_rows[m]["customers"] = cust

    if not trend_rows:
        return pd.DataFrame(columns=["month", "leads", "revenue", "customers"])

    trend_df = pd.DataFrame(list(trend_rows.values())).sort_values(by="month").reset_index(drop=True)
    return trend_df
