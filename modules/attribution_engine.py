"""
RevenueLens AI - Multi-Touch Marketing Attribution Engine
Implements 5 attribution models:
1. First-Touch Attribution
2. Last-Touch Attribution
3. Linear Attribution
4. Position-Based Attribution (U-Shaped: 40% First, 40% Last, 20% Middle)
5. Time-Decay Attribution (Exponential half-life decay)

Ensures mathematical normalization (sum of weights per customer == 1.0)
so total attributed revenue equals actual converted sales revenue.
Provides fallback when touchpoint data is unavailable.
"""

import pandas as pd
import numpy as np
from datetime import datetime


ATTRIBUTION_MODELS = [
    "First-Touch",
    "Last-Touch",
    "Linear",
    "Position-Based (U-Shaped)",
    "Time-Decay (7-Day Half-Life)"
]


def calculate_attribution(
    journey_df: pd.DataFrame,
    sales_df: pd.DataFrame,
    campaigns_df: pd.DataFrame,
    leads_df: pd.DataFrame = None,
    model: str = "Linear",
    half_life_days: float = 7.0
) -> dict:
    """
    Compute multi-touch attribution for won sales deals.
    Returns:
    {
        "channel_attribution": pd.DataFrame,
        "campaign_attribution": pd.DataFrame,
        "model_comparison": pd.DataFrame,
        "total_revenue": float,
        "is_fallback": bool
    }
    """
    if sales_df is None or sales_df.empty:
        return _empty_attribution_result()

    # Filter won deals
    won_mask = sales_df["sales_stage"].astype(str).str.lower().str.contains("won")
    won_sales = sales_df[won_mask].copy()

    if won_sales.empty:
        return _empty_attribution_result()

    total_won_rev = float(won_sales["revenue"].sum())

    # Check if journey dataset is available
    if journey_df is None or journey_df.empty or "customer_id" not in journey_df.columns:
        return _calculate_single_touch_fallback(won_sales, leads_df, campaigns_df, total_won_rev)

    # Merge journey with won sales
    merged = journey_df.merge(won_sales[["customer_id", "revenue", "close_date"]], on="customer_id", how="inner")

    if merged.empty:
        return _calculate_single_touch_fallback(won_sales, leads_df, campaigns_df, total_won_rev)

    # Sort each customer's touchpoints by timestamp
    merged["touchpoint_timestamp"] = pd.to_datetime(merged["touchpoint_timestamp"], errors="coerce")
    merged = merged.sort_values(by=["customer_id", "touchpoint_timestamp"]).reset_index(drop=True)

    # Filter out touchpoints after close_date if close_date exists
    if "close_date" in merged.columns:
        close_dt = pd.to_datetime(merged["close_date"], errors="coerce")
        valid_mask = close_dt.isna() | (merged["touchpoint_timestamp"] <= close_dt)
        if valid_mask.any():
            merged = merged[valid_mask]

    # Calculate weights for all 5 models per customer
    all_models = ["First-Touch", "Last-Touch", "Linear", "Position-Based (U-Shaped)", "Time-Decay (7-Day Half-Life)"]
    weights_records = []

    for cust_id, group in merged.groupby("customer_id"):
        n = len(group)
        rev = group["revenue"].iloc[0]
        timestamps = group["touchpoint_timestamp"].values

        # 1. First-Touch
        w_first = np.zeros(n)
        w_first[0] = 1.0

        # 2. Last-Touch
        w_last = np.zeros(n)
        w_last[-1] = 1.0

        # 3. Linear
        w_linear = np.ones(n) / float(n)

        # 4. Position-Based (U-shaped)
        w_u = np.zeros(n)
        if n == 1:
            w_u[0] = 1.0
        elif n == 2:
            w_u[0] = 0.5
            w_u[1] = 0.5
        else:
            w_u[0] = 0.4
            w_u[-1] = 0.4
            middle_count = n - 2
            w_u[1:-1] = 0.2 / middle_count

        # 5. Time-Decay
        # Weight = 2 ^ (-days_from_conversion / half_life)
        w_decay = np.ones(n)
        if n > 1 and pd.notna(timestamps[-1]):
            last_time = pd.to_datetime(timestamps[-1])
            diff_days = np.array([(last_time - pd.to_datetime(t)).total_seconds() / 86400.0 for t in timestamps])
            raw_weights = np.power(2.0, -diff_days / half_life_days)
            sum_w = raw_weights.sum()
            w_decay = raw_weights / sum_w if sum_w > 0 else np.ones(n) / float(n)

        for idx, (row_idx, row) in enumerate(group.iterrows()):
            weights_records.append({
                "customer_id": cust_id,
                "campaign_id": row.get("campaign_id", "Unknown"),
                "channel": row.get("channel", "Unknown"),
                "deal_revenue": rev,
                "weight_first": w_first[idx],
                "weight_last": w_last[idx],
                "weight_linear": w_linear[idx],
                "weight_u": w_u[idx],
                "weight_decay": w_decay[idx],
            })

    weights_df = pd.DataFrame(weights_records)

    # Calculate attributed revenues
    weights_df["rev_first"] = weights_df["deal_revenue"] * weights_df["weight_first"]
    weights_df["rev_last"] = weights_df["deal_revenue"] * weights_df["weight_last"]
    weights_df["rev_linear"] = weights_df["deal_revenue"] * weights_df["weight_linear"]
    weights_df["rev_u"] = weights_df["deal_revenue"] * weights_df["weight_u"]
    weights_df["rev_decay"] = weights_df["deal_revenue"] * weights_df["weight_decay"]

    # Select chosen model column
    model_col_map = {
        "First-Touch": "rev_first",
        "Last-Touch": "rev_last",
        "Linear": "rev_linear",
        "Position-Based (U-Shaped)": "rev_u",
        "Time-Decay (7-Day Half-Life)": "rev_decay"
    }
    selected_rev_col = model_col_map.get(model, "rev_linear")

    # Group by Channel
    channel_attr = weights_df.groupby("channel")[selected_rev_col].sum().reset_index()
    channel_attr.columns = ["channel", "attributed_revenue"]
    channel_attr["revenue_share_pct"] = (channel_attr["attributed_revenue"] / total_won_rev * 100.0).round(2)

    # Group by Campaign
    campaign_attr = weights_df.groupby("campaign_id")[selected_rev_col].sum().reset_index()
    campaign_attr.columns = ["campaign_id", "attributed_revenue"]
    campaign_attr["revenue_share_pct"] = (campaign_attr["attributed_revenue"] / total_won_rev * 100.0).round(2)

    # Join campaign metadata (spend, channel, name)
    if campaigns_df is not None and not campaigns_df.empty:
        campaign_attr = campaign_attr.merge(
            campaigns_df[["campaign_id", "campaign_name", "channel", "spend"]],
            on="campaign_id",
            how="right"
        )
        campaign_attr["attributed_revenue"] = campaign_attr["attributed_revenue"].fillna(0.0)
        campaign_attr["revenue_share_pct"] = campaign_attr["revenue_share_pct"].fillna(0.0)
        campaign_attr["spend"] = campaign_attr["spend"].fillna(0.0)
        campaign_attr["roas"] = np.where(campaign_attr["spend"] > 0, (campaign_attr["attributed_revenue"] / campaign_attr["spend"]).round(2), 0.0)
        campaign_attr["roi_pct"] = np.where(
            campaign_attr["spend"] > 0,
            ((campaign_attr["attributed_revenue"] - campaign_attr["spend"]) / campaign_attr["spend"] * 100.0).round(2),
            0.0
        )

        # Spend by channel
        channel_spend = campaigns_df.groupby("channel")["spend"].sum().reset_index()
        channel_attr = channel_attr.merge(channel_spend, on="channel", how="left").fillna(0.0)
        channel_attr["roas"] = np.where(channel_attr["spend"] > 0, (channel_attr["attributed_revenue"] / channel_attr["spend"]).round(2), 0.0)
        channel_attr["roi_pct"] = np.where(
            channel_attr["spend"] > 0,
            ((channel_attr["attributed_revenue"] - channel_attr["spend"]) / channel_attr["spend"] * 100.0).round(2),
            0.0
        )

    # Customers acquired by channel
    customers_per_channel = weights_df[weights_df[selected_rev_col] > 0].groupby("channel")["customer_id"].nunique().reset_index()
    customers_per_channel.columns = ["channel", "customers_acquired"]
    channel_attr = channel_attr.merge(customers_per_channel, on="channel", how="left").fillna(0)
    channel_attr["cac"] = np.where(
        channel_attr["customers_acquired"] > 0,
        (channel_attr["spend"] / channel_attr["customers_acquired"]).round(2),
        0.0
    )

    # Model comparison across channels
    comp_df = weights_df.groupby("channel").agg({
        "rev_first": "sum",
        "rev_last": "sum",
        "rev_linear": "sum",
        "rev_u": "sum",
        "rev_decay": "sum"
    }).reset_index()
    comp_df.columns = ["channel", "First-Touch", "Last-Touch", "Linear", "Position-Based", "Time-Decay"]

    return {
        "channel_attribution": channel_attr.sort_values(by="attributed_revenue", ascending=False).reset_index(drop=True),
        "campaign_attribution": campaign_attr.sort_values(by="attributed_revenue", ascending=False).reset_index(drop=True),
        "model_comparison": comp_df,
        "total_revenue": total_won_rev,
        "is_fallback": False
    }


def _calculate_single_touch_fallback(
    won_sales: pd.DataFrame,
    leads_df: pd.DataFrame,
    campaigns_df: pd.DataFrame,
    total_revenue: float
) -> dict:
    """
    Fallback when customer journey touchpoints are unavailable.
    Attributes revenue based directly on the lead's acquisition campaign.
    """
    if leads_df is None or leads_df.empty:
        return _empty_attribution_result()

    merged = won_sales.merge(leads_df[["customer_id", "campaign_id", "lead_source"]], on="customer_id", how="inner")
    if merged.empty:
        return _empty_attribution_result()

    channel_attr = merged.groupby("lead_source")["revenue"].sum().reset_index()
    channel_attr.columns = ["channel", "attributed_revenue"]
    channel_attr["revenue_share_pct"] = (channel_attr["attributed_revenue"] / total_revenue * 100.0).round(2)

    campaign_attr = merged.groupby("campaign_id")["revenue"].sum().reset_index()
    campaign_attr.columns = ["campaign_id", "attributed_revenue"]

    if campaigns_df is not None and not campaigns_df.empty:
        campaign_attr = campaign_attr.merge(campaigns_df[["campaign_id", "campaign_name", "channel", "spend"]], on="campaign_id", how="right").fillna(0.0)
        channel_spend = campaigns_df.groupby("channel")["spend"].sum().reset_index()
        channel_attr = channel_attr.merge(channel_spend, on="channel", how="left").fillna(0.0)

    # Identical across models in fallback
    comp_df = pd.DataFrame({
        "channel": channel_attr["channel"],
        "First-Touch": channel_attr["attributed_revenue"],
        "Last-Touch": channel_attr["attributed_revenue"],
        "Linear": channel_attr["attributed_revenue"],
        "Position-Based": channel_attr["attributed_revenue"],
        "Time-Decay": channel_attr["attributed_revenue"],
    })

    return {
        "channel_attribution": channel_attr.sort_values(by="attributed_revenue", ascending=False).reset_index(drop=True),
        "campaign_attribution": campaign_attr.sort_values(by="attributed_revenue", ascending=False).reset_index(drop=True),
        "model_comparison": comp_df,
        "total_revenue": total_revenue,
        "is_fallback": True
    }


def _empty_attribution_result() -> dict:
    return {
        "channel_attribution": pd.DataFrame(columns=["channel", "attributed_revenue", "spend", "roas", "roi_pct", "revenue_share_pct"]),
        "campaign_attribution": pd.DataFrame(columns=["campaign_id", "campaign_name", "channel", "attributed_revenue", "spend", "roas", "roi_pct"]),
        "model_comparison": pd.DataFrame(),
        "total_revenue": 0.0,
        "is_fallback": False
    }
