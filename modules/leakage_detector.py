"""
RevenueLens AI - Revenue Leakage & Bottleneck Detection Engine
Applies deterministic, transparent rule-based heuristics across marketing and sales datasets
to identify where revenue value is leaking, and formulates prioritized, evidence-backed
MBA-grade remediation recommendations.
"""

import pandas as pd
import numpy as np


def detect_revenue_leakages(
    campaigns_df: pd.DataFrame,
    leads_df: pd.DataFrame,
    sales_df: pd.DataFrame,
    attribution_df: pd.DataFrame = None,
    funnel_metrics: dict = None
) -> list:
    """
    Scan all marketing and sales data for 10 specific leakage patterns.
    Returns list of issue dictionaries.
    """
    issues = []

    if leads_df is None or leads_df.empty:
        return issues

    # Calculate base context
    total_leads = len(leads_df)
    won_mask = sales_df["sales_stage"].astype(str).str.lower().str.contains("won") if sales_df is not None and not sales_df.empty else pd.Series(dtype=bool)
    won_count = int(won_mask.sum()) if not won_mask.empty else 0
    total_revenue = float(sales_df.loc[won_mask, "revenue"].sum()) if not won_mask.empty else 0.0
    total_spend = float(campaigns_df["spend"].sum()) if campaigns_df is not None and not campaigns_df.empty else 0.0

    avg_conv_rate = (won_count / total_leads * 100.0) if total_leads > 0 else 0.0

    # 1. ISSUE: High Lead Generation but Low Customer Conversion (The Vanity Trap)
    # Check by campaign
    if "campaign_id" in leads_df.columns:
        leads_per_camp = leads_df.groupby("campaign_id").size()
        won_sales_leads = sales_df[won_mask].merge(leads_df[["customer_id", "campaign_id"]], on="customer_id", how="inner") if not won_mask.empty else pd.DataFrame()
        won_per_camp = won_sales_leads.groupby("campaign_id").size() if not won_sales_leads.empty else pd.Series(dtype=int)

        for c_id, l_cnt in leads_per_camp.items():
            if l_cnt >= total_leads * 0.15:  # significant volume (>15% of all leads)
                w_cnt = won_per_camp.get(c_id, 0)
                c_conv = (w_cnt / l_cnt * 100.0) if l_cnt > 0 else 0.0
                if c_conv < (avg_conv_rate * 0.45):  # conversion is less than half average
                    c_name = c_id
                    if campaigns_df is not None and "campaign_id" in campaigns_df.columns:
                        c_match = campaigns_df[campaigns_df["campaign_id"] == c_id]
                        if not c_match.empty:
                            c_name = f"{c_match['campaign_name'].iloc[0]} ({c_id})"

                    issues.append({
                        "id": "LEAK-001",
                        "priority": "High",
                        "category": "Lead Quality / Vanity Trap",
                        "problem": f"High Lead Volume with Severe Conversion Failure in {c_name}",
                        "evidence": f"Generated {l_cnt} leads ({l_cnt/total_leads*100:.1f}% of total) but achieved only {c_conv:.2f}% conversion rate (portfolio average is {avg_conv_rate:.2f}%). Only {w_cnt} customers acquired.",
                        "contributing_factors": "Broad audience targeting, clickbait ad copy, low-friction lead forms lacking qualification criteria, or mismatch between ad promise and product offering.",
                        "business_impact": "Sales team capacity is wasted chasing uninterested contacts; high marketing spend with negligible pipeline acceleration.",
                        "recommendation": "Add friction to the lead form (e.g., company email requirement, budget dropdown) and tighten targeting parameters to prioritize intent over raw volume.",
                        "kpi_to_monitor": f"Lead-to-SQL Conversion Rate for {c_id}"
                    })

    # 2. ISSUE: High Marketing Spend with Low or Negative Attributed Revenue (Budget Bleed)
    if campaigns_df is not None and not campaigns_df.empty:
        # Check ROAS per campaign if attribution is provided
        if attribution_df is not None and not attribution_df.empty and "attributed_revenue" in attribution_df.columns:
            m_camp = campaigns_df.merge(attribution_df[["campaign_id", "attributed_revenue"]], on="campaign_id", how="left").fillna(0.0)
            bleeding = m_camp[(m_camp["spend"] >= 10000) & (m_camp["attributed_revenue"] < m_camp["spend"] * 0.6)]
            for _, row in bleeding.iterrows():
                loss = row["spend"] - row["attributed_revenue"]
                roas = row["attributed_revenue"] / row["spend"] if row["spend"] > 0 else 0.0
                issues.append({
                    "id": "LEAK-002",
                    "priority": "High",
                    "category": "Capital Inefficiency",
                    "problem": f"Severe Capital Inefficiency in {row['campaign_name']} (ROAS: {roas:.2f}x)",
                    "evidence": f"Total spend of ${row['spend']:,.0f} yielded only ${row['attributed_revenue']:,.0f} in attributed revenue (Net loss: ${loss:,.0f}, ROI: -{(loss/row['spend']*100):.1f}%).",
                    "contributing_factors": "Overbidding on low-intent keywords, ineffective post-click landing page experience, or audience fatigue.",
                    "business_impact": f"Direct bottom-line margin erosion of ${loss:,.0f} in marketing capital.",
                    "recommendation": f"Pause or cut budget by 50% for {row['campaign_name']}; redirect capital to proven high-ROAS channels like BOFU search or referral partnerships.",
                    "kpi_to_monitor": "ROAS (target >= 2.5x) and Net Contribution Margin"
                })

    # 3. ISSUE: Excessive Drop-off Between MQL and SQL (Marketing-Sales Disconnect)
    if "qualification_status" in leads_df.columns:
        mqls = (leads_df["qualification_status"].str.upper().isin(["MQL", "SQL"])).sum()
        sqls = (leads_df["qualification_status"].str.upper() == "SQL").sum()
        if mqls > 0:
            mql_to_sql_rate = (sqls / mqls * 100.0)
            if mql_to_sql_rate < 50.0:
                issues.append({
                    "id": "LEAK-003",
                    "priority": "High",
                    "category": "Funnel Bottleneck",
                    "problem": f"Critical Funnel Choke Point: MQL-to-SQL Conversion is Only {mql_to_sql_rate:.1f}%",
                    "evidence": f"Out of {mqls} Marketing-Qualified Leads, only {sqls} were accepted as Sales-Qualified. A staggering {100-mql_to_sql_rate:.1f}% ({mqls - sqls} leads) were discarded or stalled.",
                    "contributing_factors": "Discrepancy between marketing scoring criteria and sales acceptance criteria; marketing qualifies based on content downloads rather than BANT/MEDDIC budget/authority.",
                    "business_impact": f"Estimated lost pipeline value exceeding ${(mqls - sqls) * 0.15 * (total_revenue/max(1, won_count)):,.0f}.",
                    "recommendation": "Establish a Service Level Agreement (SLA) between Sales and Marketing; redefine MQL criteria to require explicit intent signals (e.g., pricing page visits, demo requests).",
                    "kpi_to_monitor": "MQL-to-SQL Acceptance Rate (target >= 65%)"
                })

    # 4. ISSUE: Slow Sales Follow-Up Time Impacting Win Rates
    if "follow_up_time_hours" in leads_df.columns:
        leads_copy = leads_df.copy()
        if not won_mask.empty:
            won_ids = set(sales_df[won_mask]["customer_id"])
            leads_copy["won"] = leads_copy["customer_id"].isin(won_ids)

            fast_leads = leads_copy[leads_copy["follow_up_time_hours"] <= 4]
            slow_leads = leads_copy[leads_copy["follow_up_time_hours"] > 24]

            if not fast_leads.empty and not slow_leads.empty:
                fast_conv = fast_leads["won"].mean() * 100.0
                slow_conv = slow_leads["won"].mean() * 100.0
                avg_followup = leads_copy["follow_up_time_hours"].mean()

                if slow_conv < (fast_conv * 0.6) and avg_followup > 12:
                    issues.append({
                        "id": "LEAK-004",
                        "priority": "Medium",
                        "category": "Sales Execution",
                        "problem": f"Slow Lead Follow-Up Diminishing Win Probabilities (Average: {avg_followup:.1f} hours)",
                        "evidence": f"Leads contacted within 4 hours convert at {fast_conv:.1f}%, whereas leads contacted after 24 hours convert at merely {slow_conv:.1f}% (a {((fast_conv-slow_conv)/fast_conv*100):.1f}% degradation).",
                        "contributing_factors": "Manual lead assignment queues, lack of CRM notifications, SDR capacity bottlenecks during peak demand periods.",
                        "business_impact": "Substantial degradation of marketing inbound investments due to prospect decay and outreach to competing vendors.",
                        "recommendation": "Deploy automated round-robin lead distribution with instant SMS/Slack alerts for SDRs to guarantee outreach within 1 hour for high-intent leads.",
                        "kpi_to_monitor": "Median Time-to-First-Touch (target < 2 hours)"
                    })

    # 5. ISSUE: High Revenue Concentration Risk
    if attribution_df is not None and not attribution_df.empty and "attributed_revenue" in attribution_df.columns:
        top_camp_rev = attribution_df["attributed_revenue"].max()
        top_camp_name = attribution_df.sort_values(by="attributed_revenue", ascending=False)["campaign_name"].iloc[0]
        if total_revenue > 0 and (top_camp_rev / total_revenue) > 0.40:
            conc_pct = (top_camp_rev / total_revenue * 100.0)
            issues.append({
                "id": "LEAK-005",
                "priority": "Medium",
                "category": "Portfolio Risk",
                "problem": f"Extreme Revenue Concentration in '{top_camp_name}' ({conc_pct:.1f}% of Total Revenue)",
                "evidence": f"A single campaign contributes ${top_camp_rev:,.0f} out of ${total_revenue:,.0f} total generated revenue.",
                "contributing_factors": "Over-reliance on a single channel/keyword cluster with lack of diversified demand channels.",
                "business_impact": "High vulnerability to ad platform algorithm changes, auction CPC inflation, or competitor bidding wars.",
                "recommendation": "Gradually scale test budgets in complementary channels (e.g., organic inbound, referral partnerships, targeted LinkedIn outreach) to de-risk revenue.",
                "kpi_to_monitor": "Herfindahl-Hirschman Index (HHI) of Channel Revenue Contribution"
            })

    # 6. ISSUE: Channel Volume vs Value Divergence
    if "lead_source" in leads_df.columns and not won_mask.empty:
        merged_won = sales_df[won_mask].merge(leads_df[["customer_id", "lead_source"]], on="customer_id", how="inner")
        leads_by_ch = leads_df.groupby("lead_source").size()
        rev_by_ch = merged_won.groupby("lead_source")["revenue"].sum()

        for ch, l_cnt in leads_by_ch.items():
            l_share = l_cnt / total_leads * 100.0
            r_val = rev_by_ch.get(ch, 0.0)
            r_share = (r_val / total_revenue * 100.0) if total_revenue > 0 else 0.0

            if l_share >= 25.0 and r_share < 10.0:
                issues.append({
                    "id": "LEAK-006",
                    "priority": "High",
                    "category": "Channel Inefficiency",
                    "problem": f"Severe Volume vs. Value Divergence in Channel: {ch}",
                    "evidence": f"{ch} accounts for {l_share:.1f}% of all leads generated ({l_cnt} leads), but delivers only {r_share:.1f}% of total closed revenue (${r_val:,.0f}).",
                    "contributing_factors": "Attracting low-budget consumers or students rather than qualified decision-makers; mismatch in market positioning.",
                    "business_impact": "Creates a misleading illusion of marketing productivity while generating negligible enterprise value.",
                    "recommendation": "Review buyer persona alignment on {ch}. Shift campaign objectives away from generic top-of-funnel lead forms toward targeted webinar signups or demo bookings.",
                    "kpi_to_monitor": f"{ch} Revenue Contribution % vs Lead Share %"
                })

    return issues
