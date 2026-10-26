"""
RevenueLens AI - Funnel Analysis Engine
Analyzes the 9-stage marketing and sales customer journey, calculates stage-to-stage
conversion rates, drop-off rates, lost prospects, and estimated lost revenue opportunity.
Provides breakdowns by campaign, channel, and customer segment.
"""

import pandas as pd
import numpy as np


FUNNEL_STAGES = [
    "1. Impressions",
    "2. Ad Clicks",
    "3. Website Visits",
    "4. Leads Generated",
    "5. Marketing-Qualified (MQL)",
    "6. Sales-Qualified (SQL)",
    "7. Sales Opportunities",
    "8. Closed-Won Customers",
    "9. Revenue Generated"
]


def calculate_funnel_stages(
    campaigns_df: pd.DataFrame,
    leads_df: pd.DataFrame,
    journey_df: pd.DataFrame,
    sales_df: pd.DataFrame,
) -> dict:
    """
    Calculate counts, conversion rates, drop-offs, and lost value for all 9 stages.
    """
    # 1. Impressions
    impr = int(campaigns_df["impressions"].sum()) if campaigns_df is not None and "impressions" in campaigns_df.columns else 0

    # 2. Clicks
    clicks = int(campaigns_df["clicks"].sum()) if campaigns_df is not None and "clicks" in campaigns_df.columns else 0

    # 3. Website visits (from journey if available, else estimated from clicks ~ 88% click-to-visit landing rate)
    if journey_df is not None and not journey_df.empty and "touchpoint_type" in journey_df.columns:
        visits_count = int((journey_df["touchpoint_type"].str.lower().str.contains("visit|landing|web")).sum())
        if visits_count == 0:
            visits_count = int(clicks * 0.88)
    else:
        visits_count = int(clicks * 0.88)

    # 4. Leads
    leads_count = len(leads_df) if leads_df is not None else 0

    # 5. MQL
    mql_count = 0
    if leads_df is not None and not leads_df.empty and "qualification_status" in leads_df.columns:
        mql_count = int((leads_df["qualification_status"].str.upper().isin(["MQL", "SQL"])).sum())

    # 6. SQL
    sql_count = 0
    if leads_df is not None and not leads_df.empty and "qualification_status" in leads_df.columns:
        sql_count = int((leads_df["qualification_status"].str.upper() == "SQL").sum())

    # 7. Opportunities
    opps_count = len(sales_df) if sales_df is not None else 0

    # 8. Won Customers
    won_customers = 0
    total_revenue = 0.0
    if sales_df is not None and not sales_df.empty and "sales_stage" in sales_df.columns:
        won_mask = sales_df["sales_stage"].astype(str).str.lower().str.contains("won")
        won_customers = int(won_mask.sum())
        total_revenue = float(sales_df.loc[won_mask, "revenue"].sum())

    avg_deal_value = (total_revenue / won_customers) if won_customers > 0 else 10000.0

    raw_stages = [
        {"stage": "1. Impressions", "count": impr, "type": "count"},
        {"stage": "2. Ad Clicks", "count": clicks, "type": "count"},
        {"stage": "3. Website Visits", "count": visits_count, "type": "count"},
        {"stage": "4. Leads Generated", "count": leads_count, "type": "count"},
        {"stage": "5. Marketing-Qualified (MQL)", "count": mql_count, "type": "count"},
        {"stage": "6. Sales-Qualified (SQL)", "count": sql_count, "type": "count"},
        {"stage": "7. Sales Opportunities", "count": opps_count, "type": "count"},
        {"stage": "8. Closed-Won Customers", "count": won_customers, "type": "count"},
    ]

    # Calculate step-by-step metrics
    table_rows = []
    # Benchmark downstream conversion to won deal from each stage
    downstream_deal_probs = [
        (won_customers / impr) if impr > 0 else 0,
        (won_customers / clicks) if clicks > 0 else 0,
        (won_customers / visits_count) if visits_count > 0 else 0,
        (won_customers / leads_count) if leads_count > 0 else 0,
        (won_customers / mql_count) if mql_count > 0 else 0,
        (won_customers / sql_count) if sql_count > 0 else 0,
        (won_customers / opps_count) if opps_count > 0 else 0,
        1.0
    ]

    for i, s in enumerate(raw_stages):
        curr_cnt = s["count"]
        if i == 0:
            conv_prev = 100.0
            drop_off_pct = 0.0
            lost_prospects = 0
            lost_revenue = 0.0
        else:
            prev_cnt = raw_stages[i - 1]["count"]
            conv_prev = (curr_cnt / prev_cnt * 100.0) if prev_cnt > 0 else 0.0
            drop_off_pct = max(0.0, 100.0 - conv_prev) if prev_cnt > 0 else 0.0
            lost_prospects = max(0, prev_cnt - curr_cnt)
            # Estimated revenue opportunity lost: lost prospects * historical win prob from that stage * avg deal
            win_prob = downstream_deal_probs[i]
            lost_revenue = lost_prospects * win_prob * avg_deal_value

        table_rows.append({
            "stage_index": i + 1,
            "stage_name": s["stage"],
            "count": curr_cnt,
            "conversion_from_prev_pct": round(conv_prev, 2),
            "drop_off_pct": round(drop_off_pct, 2),
            "lost_prospects": lost_prospects,
            "lost_revenue_opportunity": round(lost_revenue, 2),
        })

    funnel_df = pd.DataFrame(table_rows)

    # Identify major bottlenecks (ignore impressions to clicks as standard CTR is naturally ~1-3%)
    sales_funnel_df = funnel_df.iloc[3:].copy()  # from Leads onwards
    max_drop_stage = sales_funnel_df.loc[sales_funnel_df["drop_off_pct"].idxmax()]["stage_name"] if not sales_funnel_df.empty else "N/A"
    max_value_lost_stage = sales_funnel_df.loc[sales_funnel_df["lost_revenue_opportunity"].idxmax()]["stage_name"] if not sales_funnel_df.empty else "N/A"

    return {
        "funnel_df": funnel_df,
        "raw_counts": {s["stage"]: s["count"] for s in raw_stages},
        "total_revenue": total_revenue,
        "avg_deal_value": avg_deal_value,
        "max_drop_stage": max_drop_stage,
        "max_value_lost_stage": max_value_lost_stage
    }


def get_funnel_stage_breakdown(
    stage_name: str,
    campaigns_df: pd.DataFrame,
    leads_df: pd.DataFrame,
    sales_df: pd.DataFrame
) -> dict:
    """
    Break down a selected funnel stage by Campaign, Channel, and Industry Segment.
    """
    breakdown_by_channel = pd.DataFrame()
    breakdown_by_campaign = pd.DataFrame()
    breakdown_by_industry = pd.DataFrame()

    stage_clean = stage_name.lower()

    if "impression" in stage_clean:
        if campaigns_df is not None and not campaigns_df.empty:
            breakdown_by_channel = campaigns_df.groupby("channel")["impressions"].sum().reset_index()
            breakdown_by_campaign = campaigns_df.groupby("campaign_name")["impressions"].sum().reset_index()

    elif "click" in stage_clean:
        if campaigns_df is not None and not campaigns_df.empty:
            breakdown_by_channel = campaigns_df.groupby("channel")["clicks"].sum().reset_index()
            breakdown_by_campaign = campaigns_df.groupby("campaign_name")["clicks"].sum().reset_index()

    elif "lead" in stage_clean or "visit" in stage_clean:
        if leads_df is not None and not leads_df.empty:
            breakdown_by_channel = leads_df.groupby("lead_source").size().reset_index(name="count")
            breakdown_by_campaign = leads_df.groupby("campaign_id").size().reset_index(name="count")
            if "industry" in leads_df.columns:
                breakdown_by_industry = leads_df.groupby("industry").size().reset_index(name="count")

    elif "mql" in stage_clean:
        if leads_df is not None and not leads_df.empty:
            mqls = leads_df[leads_df["qualification_status"].str.upper().isin(["MQL", "SQL"])]
            breakdown_by_channel = mqls.groupby("lead_source").size().reset_index(name="count")
            breakdown_by_campaign = mqls.groupby("campaign_id").size().reset_index(name="count")
            if "industry" in mqls.columns:
                breakdown_by_industry = mqls.groupby("industry").size().reset_index(name="count")

    elif "sql" in stage_clean:
        if leads_df is not None and not leads_df.empty:
            sqls = leads_df[leads_df["qualification_status"].str.upper() == "SQL"]
            breakdown_by_channel = sqls.groupby("lead_source").size().reset_index(name="count")
            breakdown_by_campaign = sqls.groupby("campaign_id").size().reset_index(name="count")
            if "industry" in sqls.columns:
                breakdown_by_industry = sqls.groupby("industry").size().reset_index(name="count")

    elif "opp" in stage_clean or "won" in stage_clean or "closed" in stage_clean:
        if sales_df is not None and not sales_df.empty and leads_df is not None:
            merged = sales_df.merge(leads_df, on="customer_id", how="inner")
            if "won" in stage_clean or "closed" in stage_clean:
                merged = merged[merged["sales_stage"].astype(str).str.lower().str.contains("won")]

            breakdown_by_channel = merged.groupby("lead_source").size().reset_index(name="count")
            breakdown_by_campaign = merged.groupby("campaign_id").size().reset_index(name="count")
            if "industry" in merged.columns:
                breakdown_by_industry = merged.groupby("industry").size().reset_index(name="count")

    # Standardize channel column name
    if not breakdown_by_channel.empty and "lead_source" in breakdown_by_channel.columns:
        breakdown_by_channel = breakdown_by_channel.rename(columns={"lead_source": "channel"})

    # Map campaign IDs to names if available
    if not breakdown_by_campaign.empty and "campaign_id" in breakdown_by_campaign.columns and campaigns_df is not None:
        c_map = dict(zip(campaigns_df["campaign_id"], campaigns_df["campaign_name"]))
        breakdown_by_campaign["campaign_name"] = breakdown_by_campaign["campaign_id"].map(c_map).fillna(breakdown_by_campaign["campaign_id"])

    return {
        "channel": breakdown_by_channel,
        "campaign": breakdown_by_campaign,
        "industry": breakdown_by_industry
    }
