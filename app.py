"""
RevenueLens AI - Marketing-to-Revenue Attribution & Funnel Intelligence
Main Streamlit Application Entrypoint
"""

import os
import io
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, date

# Local Modules
from modules.data_loader import (
    load_data_from_db, generate_synthetic_data, save_to_sqlite,
    validate_datasets, SAMPLE_DIR, TEMPLATES_DIR
)
from modules.kpi_engine import (
    filter_data, calculate_executive_kpis, calculate_period_comparison
)
from modules.funnel_engine import (
    calculate_funnel_stages, get_funnel_stage_breakdown
)
from modules.attribution_engine import (
    calculate_attribution, ATTRIBUTION_MODELS
)
from modules.campaign_analytics import (
    compute_campaign_metrics, compute_monthly_trends
)
from modules.lead_ml_engine import (
    train_lead_conversion_models, predict_single_lead
)
from modules.leakage_detector import detect_revenue_leakages
from modules.scenario_simulator import simulate_marketing_scenario
from modules.ai_insights import (
    generate_strategic_action_plan, generate_executive_narrative
)
from modules.pdf_reporter import generate_executive_pdf_report


# Page Configuration
st.set_page_config(
    page_title="RevenueLens AI | Marketing-to-Revenue Intelligence",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom SaaS Styling (CSS)
st.markdown("""
<style>
    /* Metric Card Styling */
    .metric-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        margin-bottom: 12px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .metric-title {
        color: #64748B;
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .metric-value {
        color: #0F172A;
        font-size: 1.65rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .metric-delta-pos {
        color: #10B981;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .metric-delta-neg {
        color: #EF4444;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .metric-delta-neutral {
        color: #64748B;
        font-size: 0.8rem;
    }

    /* Badge & Alert Styling */
    .badge-high {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-med {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-low {
        background-color: #E0E7FF;
        color: #3730A3;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    /* Section Cards */
    .section-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }

    /* Sub-header text */
    .subtext {
        color: #475569;
        font-size: 0.95rem;
        margin-top: -8px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
@st.cache_data(ttl=3600)
def get_initial_data():
    return load_data_from_db()


if "datasets" not in st.session_state:
    st.session_state.datasets = get_initial_data()

if "openai_api_key" not in st.session_state:
    st.session_state.openai_api_key = os.getenv("OPENAI_API_KEY", "")


# SIDEBAR: NAVIGATION & GLOBAL FILTERS
with st.sidebar:
    st.markdown("### 🎯 **RevenueLens AI**")
    st.caption("Marketing-to-Revenue Attribution & Funnel Intelligence")
    st.markdown("---")

    # Navigation Menu
    pages = [
        "1. Executive Overview",
        "2. Funnel Analysis",
        "3. Revenue Attribution",
        "4. Campaign Performance",
        "5. Lead Intelligence & ML",
        "6. AI Insights & Leakage",
        "7. Scenario Simulator",
        "8. Data Management & Upload",
        "9. Methodology & Definitions"
    ]
    selected_page = st.radio("Navigation", pages, label_visibility="collapsed")
    st.markdown("---")

    # Global Filters Section
    st.markdown("#### 🔍 **Global Filters**")

    c_raw = st.session_state.datasets.get("campaigns", pd.DataFrame())
    l_raw = st.session_state.datasets.get("leads", pd.DataFrame())

    # Date Range Filter
    min_date = date(2025, 1, 1)
    max_date = date(2025, 7, 30)
    if not l_raw.empty and "lead_date" in l_raw.columns:
        valid_dates = pd.to_datetime(l_raw["lead_date"], errors="coerce").dropna()
        if not valid_dates.empty:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()

    selected_date_range = st.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Channel Filter
    all_channels = sorted(list(c_raw["channel"].unique())) if not c_raw.empty and "channel" in c_raw.columns else []
    selected_channels = st.multiselect("Marketing Channels", options=all_channels, default=all_channels)

    # Campaign Filter
    campaign_options = sorted(list(c_raw["campaign_id"].unique())) if not c_raw.empty and "campaign_id" in c_raw.columns else []
    camp_name_map = dict(zip(c_raw["campaign_id"], c_raw["campaign_name"])) if not c_raw.empty else {}
    selected_campaigns = st.multiselect(
        "Campaigns",
        options=campaign_options,
        default=[],
        format_func=lambda x: f"{camp_name_map.get(x, x)} ({x})"
    )

    # Industry / Customer Segment
    all_industries = sorted(list(l_raw["industry"].dropna().unique())) if not l_raw.empty and "industry" in l_raw.columns else []
    selected_industries = st.multiselect("Industry Segments", options=all_industries, default=all_industries)

    # Campaign Objective Filter
    all_objectives = sorted(list(c_raw["campaign_objective"].dropna().unique())) if not c_raw.empty and "campaign_objective" in c_raw.columns else []
    selected_objectives = st.multiselect("Campaign Objectives", options=all_objectives, default=all_objectives)

    st.markdown("---")
    # LLM Key Configuration
    with st.expander("🔑 AI / LLM Configuration"):
        api_key_input = st.text_input("OpenAI API Key", value=st.session_state.openai_api_key, type="password")
        if api_key_input != st.session_state.openai_api_key:
            st.session_state.openai_api_key = api_key_input
            st.success("API key updated.")
        st.caption("Leave blank to use the deterministic rule-based insights engine (100% offline).")


# Apply Global Filters to Datasets
date_filter_arg = selected_date_range if (isinstance(selected_date_range, (tuple, list)) and len(selected_date_range) == 2) else None

campaigns_df, leads_df, journey_df, sales_df = filter_data(
    st.session_state.datasets.get("campaigns"),
    st.session_state.datasets.get("leads"),
    st.session_state.datasets.get("customer_journey"),
    st.session_state.datasets.get("sales"),
    date_range=date_filter_arg,
    selected_campaigns=selected_campaigns if selected_campaigns else None,
    selected_channels=selected_channels if len(selected_channels) < len(all_channels) else None,
    selected_industries=selected_industries if len(selected_industries) < len(all_industries) else None,
    selected_objectives=selected_objectives if len(selected_objectives) < len(all_objectives) else None,
)

# Compute Core Metrics and Caches
kpis = calculate_executive_kpis(campaigns_df, leads_df, sales_df)
period_comp = calculate_period_comparison(campaigns_df, leads_df, sales_df)
funnel_data = calculate_funnel_stages(campaigns_df, leads_df, journey_df, sales_df)
attribution_linear = calculate_attribution(journey_df, sales_df, campaigns_df, leads_df, model="Linear")
campaign_metrics_df = compute_campaign_metrics(campaigns_df, leads_df, sales_df, attribution_linear.get("campaign_attribution"))
leakage_issues = detect_revenue_leakages(campaigns_df, leads_df, sales_df, attribution_linear.get("campaign_attribution"), funnel_data)
action_plan = generate_strategic_action_plan(leakage_issues, campaign_metrics_df, funnel_data, None, attribution_linear)


# Helper function to render KPI Card
def render_kpi_card(title: str, value_str: str, metric_key: str, tooltip: str = ""):
    delta_info = period_comp.get(metric_key, {})
    delta_pct = delta_info.get("delta_pct", 0.0)
    is_pos_good = delta_info.get("is_positive_good", True)

    if delta_pct > 0:
        cls_name = "metric-delta-pos" if is_pos_good else "metric-delta-neg"
        delta_str = f"▲ +{delta_pct:.1f}% vs prior period"
    elif delta_pct < 0:
        cls_name = "metric-delta-neg" if is_pos_good else "metric-delta-pos"
        delta_str = f"▼ {delta_pct:.1f}% vs prior period"
    else:
        cls_name = "metric-delta-neutral"
        delta_str = "● 0.0% vs prior period"

    html = f"""
    <div class="metric-card" title="{tooltip}">
        <div class="metric-title">{title}</div>
        <div class="metric-value">{value_str}</div>
        <div class="{cls_name}">{delta_str}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


# ==============================================================================
# PAGE 1: EXECUTIVE OVERVIEW
# ==============================================================================
if selected_page == "1. Executive Overview":
    st.title("📊 Executive Dashboard")
    st.markdown('<div class="subtext">High-level marketing performance, revenue velocity, unit economics, and growth bottleneck overview.</div>', unsafe_allow_html=True)

    # Top Row: Financial & ROI KPIs
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_kpi_card("Total Marketing Spend", f"${kpis['spend']:,.0f}", "spend", "Aggregate gross marketing investment across filtered campaigns.")
    with c2:
        render_kpi_card("Attributed Revenue", f"${kpis['revenue']:,.0f}", "revenue", "Total closed-won sales revenue linked to marketing touchpoints.")
    with c3:
        render_kpi_card("Return on Ad Spend (ROAS)", f"{kpis['roas']:.2f}x", "roas", "Attributed Revenue / Marketing Spend.")
    with c4:
        render_kpi_card("Marketing ROI", f"{kpis['roi']:+.1f}%", "roi", "(Attributed Revenue - Spend) / Spend * 100.")
    with c5:
        render_kpi_card("Average Deal Value (ACV)", f"${kpis['avg_deal_value']:,.0f}", "avg_deal_value", "Total Revenue / Customers Acquired.")

    # Second Row: Volume & Conversion KPIs
    c6, c7, c8, c9, c10 = st.columns(5)
    with c6:
        render_kpi_card("Campaign Impressions", f"{kpis['impressions']:,}", "impressions", "Total top-of-funnel ad views.")
    with c7:
        render_kpi_card("Total Ad Clicks", f"{kpis['clicks']:,}", "clicks", "Total user clicks on ad creatives (CTR: " + f"{kpis['ctr']:.2f}%)")
    with c8:
        render_kpi_card("Leads Generated", f"{kpis['leads']:,}", "leads", "Total inbound form fills and contact captures.")
    with c9:
        render_kpi_card("Customers Acquired", f"{kpis['customers']:,}", "customers", "Closed-Won paying accounts.")
    with c10:
        render_kpi_card("Lead-to-Customer Conv.", f"{kpis['conversion_rate']:.2f}%", "conversion_rate", "Percentage of leads that successfully converted into won accounts.")

    # Third Row: Unit Economics
    c11, c12, c13, c14, c15 = st.columns(5)
    with c11:
        render_kpi_card("Cost Per Lead (CPL)", f"${kpis['cpl']:.2f}", "cpl", "Marketing Spend / Leads Generated.")
    with c12:
        render_kpi_card("Customer Acq. Cost (CAC)", f"${kpis['cac']:,.2f}", "cac", "Marketing Spend / Won Customers.")
    with c13:
        render_kpi_card("MQL Count", f"{kpis['mql']:,}", "mql", "Marketing-Qualified Leads meeting scoring threshold.")
    with c14:
        render_kpi_card("SQL Count", f"{kpis['sql']:,}", "sql", "Sales-Qualified Leads accepted by the sales team.")
    with c15:
        render_kpi_card("Revenue Per Lead", f"${kpis['revenue_per_lead']:.2f}", "revenue_per_lead", "Attributed Revenue / Total Leads.")

    st.markdown("---")

    # Middle Section: Visual Comparison Charts
    col_chart1, col_chart2 = st.columns([1, 1])

    with col_chart1:
        st.subheader("Spend vs. Attributed Revenue by Channel")
        ch_attr = attribution_linear.get("channel_attribution", pd.DataFrame())
        if not ch_attr.empty and "spend" in ch_attr.columns:
            plot_df = ch_attr.melt(id_vars=["channel"], value_vars=["spend", "attributed_revenue"], var_name="Metric", value_name="Amount")
            plot_df["Metric"] = plot_df["Metric"].map({"spend": "Spend ($)", "attributed_revenue": "Revenue ($)"})
            fig = px.bar(
                plot_df, x="channel", y="Amount", color="Metric",
                barmode="group",
                color_discrete_map={"Spend ($)": "#94A3B8", "Revenue ($)": "#2563EB"},
                labels={"Amount": "USD ($)", "channel": "Marketing Channel"}
            )
            fig.update_layout(legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1), margin=dict(l=20, r=20, t=30, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No channel financial data available.")

    with col_chart2:
        st.subheader("Monthly Lead Generation & Revenue Velocity")
        trends = compute_monthly_trends(leads_df, sales_df)
        if not trends.empty:
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=trends["month"], y=trends["leads"], name="Leads Generated", marker_color="#93C5FD", yaxis="y1"))
            fig2.add_trace(go.Scatter(x=trends["month"], y=trends["revenue"], name="Revenue ($)", mode="lines+markers", line=dict(color="#1E3A8A", width=3), yaxis="y2"))
            fig2.update_layout(
                yaxis=dict(title="Leads Generated", side="left", showgrid=False),
                yaxis2=dict(title="Revenue ($)", side="right", overlaying="y", showgrid=True),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=20, r=20, t=30, b=20)
            )
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No chronological trend data found.")

    # Bottom Section: Critical Bottleneck Alert Banners
    st.markdown("### 🚨 **Critical Funnel Bottlenecks & Leaks**")
    if leakage_issues:
        top_issues = [i for i in leakage_issues if i.get("priority") == "High"][:2]
        if not top_issues:
            top_issues = leakage_issues[:2]

        for issue in top_issues:
            with st.container():
                st.error(f"**[{issue.get('priority')} PRIORITY] {issue.get('problem')}**\n\n"
                         f"• **Empirical Evidence:** {issue.get('evidence')}\n\n"
                         f"• **Immediate MBA Action:** {issue.get('recommendation')}")
    else:
        st.success("No high-severity revenue leakages detected under current filters.")


# ==============================================================================
# PAGE 2: FUNNEL ANALYSIS
# ==============================================================================
elif selected_page == "2. Funnel Analysis":
    st.title("🌪️ Customer Journey & Funnel Intelligence")
    st.markdown('<div class="subtext">9-Stage Marketing-to-Revenue Conversion Funnel, Stage Drop-offs, Lost Prospects, and Dollar Value Lost.</div>', unsafe_allow_html=True)

    funnel_df = funnel_data.get("funnel_df", pd.DataFrame())

    if not funnel_df.empty:
        # 1. Interactive Plotly Funnel Chart
        funnel_fig = go.Figure(go.Funnel(
            y=funnel_df["stage_name"],
            x=funnel_df["count"],
            textinfo="value+percent previous",
            marker=dict(color=["#1E3A8A", "#2563EB", "#3B82F6", "#60A5FA", "#93C5FD", "#F59E0B", "#10B981", "#059669"])
        ))
        funnel_fig.update_layout(
            title="End-to-End Customer Journey Volume & Stage Transition Rates",
            margin=dict(l=20, r=20, t=50, b=20)
        )
        st.plotly_chart(funnel_fig, use_container_width=True)

        # Highlight Key Funnel Insights
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            st.metric("Worst Stage Drop-Off", funnel_data.get("max_drop_stage", "N/A"))
        with f_col2:
            st.metric("Largest Revenue Opportunity Lost", funnel_data.get("max_value_lost_stage", "N/A"))
        with f_col3:
            st.metric("Total Attributed Closed Revenue", f"${funnel_data.get('total_revenue', 0):,.0f}")

        # 2. Stage-by-Stage Detailed Metrics Table
        st.markdown("### 📋 Stage Transition & Opportunity Cost Breakdown")
        display_funnel = funnel_df.copy()
        display_funnel.columns = [
            "Stage #", "Stage Name", "Volume", "Conv. from Prior (%)",
            "Drop-off (%)", "Lost Prospects", "Est. Lost Revenue Opportunity ($)"
        ]
        display_funnel["Volume"] = display_funnel["Volume"].apply(lambda x: f"{int(x):,}")
        display_funnel["Lost Prospects"] = display_funnel["Lost Prospects"].apply(lambda x: f"{int(x):,}")
        display_funnel["Est. Lost Revenue Opportunity ($)"] = display_funnel["Est. Lost Revenue Opportunity ($)"].apply(lambda x: f"${x:,.0f}")
        st.dataframe(display_funnel, use_container_width=True, hide_index=True)

        # 3. Interactive Stage Drill-down
        st.markdown("---")
        st.markdown("### 🔍 **Funnel Stage Deep Dive**")
        selected_drill_stage = st.selectbox(
            "Select Funnel Stage to Analyze Performance Drivers:",
            options=funnel_df["stage_name"].tolist(),
            index=3  # Default to Leads Generated
        )

        breakdown = get_funnel_stage_breakdown(selected_drill_stage, campaigns_df, leads_df, sales_df)

        d_col1, d_col2 = st.columns(2)
        with d_col1:
            st.markdown(f"**By Marketing Channel**")
            ch_data = breakdown.get("channel", pd.DataFrame())
            if not ch_data.empty and len(ch_data.columns) >= 2:
                name_col = "channel" if "channel" in ch_data.columns else ("lead_source" if "lead_source" in ch_data.columns else ch_data.columns[0])
                val_cols = [c for c in ch_data.columns if c != name_col]
                val_col = val_cols[0] if val_cols else ch_data.columns[1]
                fig_d1 = px.pie(ch_data, names=name_col, values=val_col, hole=0.45, color_discrete_sequence=px.colors.qualitative.Prism)
                fig_d1.update_layout(margin=dict(l=10, r=10, t=20, b=10))
                st.plotly_chart(fig_d1, use_container_width=True)
            else:
                st.info("No channel data for this stage.")

        with d_col2:
            st.markdown(f"**By Customer Segment / Industry**")
            ind_data = breakdown.get("industry", pd.DataFrame())
            if not ind_data.empty and len(ind_data.columns) >= 2:
                ind_col = "industry" if "industry" in ind_data.columns else ind_data.columns[0]
                val_cols2 = [c for c in ind_data.columns if c != ind_col]
                val_col2 = val_cols2[0] if val_cols2 else ind_data.columns[1]
                fig_d2 = px.bar(ind_data, x=ind_col, y=val_col2, text_auto=True, color=ind_col, color_discrete_sequence=px.colors.qualitative.Safe)
                fig_d2.update_layout(showlegend=False, margin=dict(l=10, r=10, t=20, b=10))
                st.plotly_chart(fig_d2, use_container_width=True)
            else:
                st.info("Industry breakdown not available for this stage.")

    else:
        st.warning("Insufficient funnel data available to render pipeline stages.")


# ==============================================================================
# PAGE 3: REVENUE ATTRIBUTION
# ==============================================================================
elif selected_page == "3. Revenue Attribution":
    st.title("⚖️ Marketing Attribution Engine")
    st.markdown('<div class="subtext">Multi-touch attribution models distribute revenue credit across touchpoints to reveal true channel ROI.</div>', unsafe_allow_html=True)

    # Attribution Model Selector
    attr_c1, attr_c2 = st.columns([2, 1])
    with attr_c1:
        chosen_model = st.selectbox(
            "Select Primary Attribution Model:",
            options=ATTRIBUTION_MODELS,
            index=2  # Linear
        )
    with attr_c2:
        half_life = 7.0
        if "Time-Decay" in chosen_model:
            half_life = st.slider("Time-Decay Half-Life (Days)", min_value=1.0, max_value=30.0, value=7.0, step=1.0)

    # Run attribution
    attribution_run = calculate_attribution(
        journey_df, sales_df, campaigns_df, leads_df,
        model=chosen_model, half_life_days=half_life
    )

    if attribution_run.get("is_fallback"):
        st.warning("⚠️ **Single-Touch Fallback Mode:** Customer journey touchpoint dataset is missing or unlinked. Attribution is estimated from direct lead acquisition channel.")

    ch_attr_df = attribution_run.get("channel_attribution", pd.DataFrame())
    camp_attr_df = attribution_run.get("campaign_attribution", pd.DataFrame())
    comp_df = attribution_run.get("model_comparison", pd.DataFrame())

    # Summary Metrics Row
    m_col1, m_col2, m_col3 = st.columns(3)
    with m_col1:
        st.metric("Total Attributed Closed Revenue", f"${attribution_run.get('total_revenue', 0):,.0f}")
    with m_col2:
        top_rev_ch = ch_attr_df.iloc[0]["channel"] if not ch_attr_df.empty else "N/A"
        st.metric("Top Revenue Producing Channel", top_rev_ch)
    with m_col3:
        top_roas_val = ch_attr_df["roas"].max() if (not ch_attr_df.empty and "roas" in ch_attr_df.columns) else 0.0
        st.metric("Highest Channel ROAS", f"{top_roas_val:.2f}x")

    st.markdown("---")

    # Channel Attribution Table & Chart
    attr_tab1, attr_tab2, attr_tab3 = st.tabs(["📊 Channel Attribution", "🎯 Campaign Attribution", "🔄 Multi-Model Comparison"])

    with attr_tab1:
        st.subheader(f"Channel Revenue Contribution ({chosen_model} Model)")
        if not ch_attr_df.empty:
            chart_col, table_col = st.columns([1, 1])
            with chart_col:
                fig_ch = px.bar(
                    ch_attr_df, x="channel", y="attributed_revenue",
                    color="roas",
                    color_continuous_scale="Blues",
                    labels={"attributed_revenue": "Attributed Revenue ($)", "channel": "Channel", "roas": "ROAS (x)"},
                    text_auto=".2s"
                )
                fig_ch.update_layout(margin=dict(l=10, r=10, t=30, b=10))
                st.plotly_chart(fig_ch, use_container_width=True)

            with table_col:
                display_ch = ch_attr_df.copy()
                for c in ["attributed_revenue", "spend", "cac"]:
                    if c in display_ch.columns:
                        display_ch[c] = display_ch[c].apply(lambda x: f"${x:,.0f}")
                if "roas" in display_ch.columns:
                    display_ch["roas"] = display_ch["roas"].apply(lambda x: f"{x:.2f}x")
                if "roi_pct" in display_ch.columns:
                    display_ch["roi_pct"] = display_ch["roi_pct"].apply(lambda x: f"{x:+.1f}%")
                if "revenue_share_pct" in display_ch.columns:
                    display_ch["revenue_share_pct"] = display_ch["revenue_share_pct"].apply(lambda x: f"{x:.1f}%")
                st.dataframe(display_ch, use_container_width=True, hide_index=True)
        else:
            st.info("No channel attribution data available.")

    with attr_tab2:
        st.subheader("Campaign Attribution Detail")
        if not camp_attr_df.empty:
            disp_camp = camp_attr_df.copy()
            for c in ["attributed_revenue", "spend"]:
                if c in disp_camp.columns:
                    disp_camp[c] = disp_camp[c].apply(lambda x: f"${x:,.0f}")
            if "roas" in disp_camp.columns:
                disp_camp["roas"] = disp_camp["roas"].apply(lambda x: f"{x:.2f}x")
            if "roi_pct" in disp_camp.columns:
                disp_camp["roi_pct"] = disp_camp["roi_pct"].apply(lambda x: f"{x:+.1f}%")
            st.dataframe(disp_camp, use_container_width=True, hide_index=True)
        else:
            st.info("No campaign attribution data available.")

    with attr_tab3:
        st.subheader("Side-by-Side Model Comparison (Credit Distribution Shift)")
        st.caption("Notice how First-Touch favors upper-funnel discovery (Organic/Meta), while Last-Touch credits conversion engines (Search/Email).")
        if not comp_df.empty:
            melted_comp = comp_df.melt(id_vars=["channel"], var_name="Model", value_name="Attributed Revenue ($)")
            fig_comp = px.bar(
                melted_comp, x="channel", y="Attributed Revenue ($)",
                color="Model", barmode="group",
                color_discrete_sequence=px.colors.qualitative.Dark24
            )
            fig_comp.update_layout(margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(fig_comp, use_container_width=True)

            # Data Table
            st.dataframe(comp_df.style.format({c: "${:,.0f}" for c in comp_df.columns if c != "channel"}), use_container_width=True)
        else:
            st.info("Model comparison not available.")


# ==============================================================================
# PAGE 4: CAMPAIGN PERFORMANCE
# ==============================================================================
elif selected_page == "4. Campaign Performance":
    st.title("📈 Campaign Performance Analytics")
    st.markdown('<div class="subtext">Evaluating efficiency, cost per acquisition, and categorizing campaigns into strategic performance quadrants.</div>', unsafe_allow_html=True)

    if not campaign_metrics_df.empty:
        # Quadrant Explanatory Legend
        with st.expander("ℹ️ Understanding Strategic Marketing Quadrants (MBA Framework)"):
            st.markdown("""
            - 🚨 **Vanity Trap (High Leads, Low Conversion):** Generates high lead counts at cheap CPL, but prospects fail to convert into paying deals.
            - 💎 **Hidden Gem (Low Leads, High Conversion & High ROI):** Produces modest lead volume, but leads are high intent, resulting in strong revenue contribution.
            - 💸 **Money Pit (High Spend, Negative ROI):** Significant budget drain with negligible revenue yield. Immediate pause or budget cut candidate.
            - 🚀 **Scale Candidate (Top Performer):** High volume, high conversion, and positive unit economics. Primary destination for additional capital.
            """)

        # Scatter Plot 1: Spend vs Attributed Revenue (Bubble size = Leads)
        sc1, sc2 = st.columns(2)
        with sc1:
            st.subheader("Spend vs. Attributed Revenue")
            fig_s1 = px.scatter(
                campaign_metrics_df,
                x="spend", y="attributed_revenue",
                size="leads_count", color="strategic_segment",
                hover_name="campaign_name",
                labels={"spend": "Marketing Spend ($)", "attributed_revenue": "Attributed Revenue ($)"},
                color_discrete_map={
                    "Scale Candidate (Top Performer)": "#10B981",
                    "Hidden Gem (High Intent, High ROI)": "#2563EB",
                    "Vanity Trap (High Volume, Low Quality)": "#F59E0B",
                    "Money Pit (High Spend, Negative ROI)": "#EF4444",
                    "Moderate Performer": "#94A3B8"
                }
            )
            # Add Breakeven line (y = x)
            max_val = max(campaign_metrics_df["spend"].max(), campaign_metrics_df["attributed_revenue"].max()) * 1.1
            fig_s1.add_shape(type="line", x0=0, y0=0, x1=max_val, y1=max_val, line=dict(color="gray", dash="dash"))
            fig_s1.update_layout(margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_s1, use_container_width=True)

        with sc2:
            st.subheader("Leads vs. Actual Customers Acquired")
            fig_s2 = px.scatter(
                campaign_metrics_df,
                x="leads_count", y="customers_acquired",
                color="strategic_segment",
                size="spend",
                hover_name="campaign_name",
                labels={"leads_count": "Leads Generated", "customers_acquired": "Closed Customers"},
                color_discrete_map={
                    "Scale Candidate (Top Performer)": "#10B981",
                    "Hidden Gem (High Intent, High ROI)": "#2563EB",
                    "Vanity Trap (High Volume, Low Quality)": "#F59E0B",
                    "Money Pit (High Spend, Negative ROI)": "#EF4444",
                    "Moderate Performer": "#94A3B8"
                }
            )
            fig_s2.update_layout(margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.2))
            st.plotly_chart(fig_s2, use_container_width=True)

        # CPL vs CAC Chart
        st.subheader("Unit Economics: Cost Per Lead (CPL) vs. Customer Acquisition Cost (CAC)")
        fig_unit = px.bar(
            campaign_metrics_df,
            x="campaign_name", y=["cpl", "cac"],
            barmode="group",
            labels={"value": "Cost ($)", "campaign_name": "Campaign"},
            color_discrete_map={"cpl": "#94A3B8", "cac": "#EF4444"}
        )
        fig_unit.update_layout(margin=dict(l=10, r=10, t=30, b=50), xaxis_tickangle=-30)
        st.plotly_chart(fig_unit, use_container_width=True)

        # Full Performance Table
        st.markdown("### 📋 Campaign Performance Ledger")
        disp_table = campaign_metrics_df[[
            "campaign_id", "campaign_name", "channel", "strategic_segment",
            "spend", "leads_count", "cpl", "customers_acquired", "cac",
            "lead_to_customer_pct", "attributed_revenue", "roas", "roi_pct"
        ]].copy()

        st.dataframe(
            disp_table.style.format({
                "spend": "${:,.0f}",
                "cpl": "${:,.2f}",
                "cac": "${:,.0f}",
                "attributed_revenue": "${:,.0f}",
                "lead_to_customer_pct": "{:.2f}%",
                "roas": "{:.2f}x",
                "roi_pct": "{:+.1f}%"
            }),
            use_container_width=True,
            hide_index=True
        )

        # CSV / Excel Download
        csv_data = disp_table.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Campaign Ledger (CSV)",
            data=csv_data,
            file_name="campaign_performance_ledger.csv",
            mime="text/csv"
        )
    else:
        st.warning("No campaign performance metrics found under selected filters.")


# ==============================================================================
# PAGE 5: LEAD INTELLIGENCE & MACHINE LEARNING
# ==============================================================================
elif selected_page == "5. Lead Intelligence & ML":
    st.title("🤖 Lead Quality & Conversion Intelligence")
    st.markdown('<div class="subtext">Supervised Machine Learning classification models identify key conversion drivers and score lead probability.</div>', unsafe_allow_html=True)

    with st.spinner("Training predictive lead classification models..."):
        ml_results = train_lead_conversion_models(leads_df, sales_df)

    if ml_results.get("error"):
        st.error(f"Machine Learning Pipeline Warning: {ml_results['error']}")
    else:
        models = ml_results["models"]
        best_model = ml_results["best_model_name"]

        # 1. Model Evaluation Metrics
        st.subheader("Model Evaluation & Diagnostic Benchmarks")
        st.caption(f"Trained on {ml_results['train_sample_size']} leads, validated on {ml_results['test_sample_size']} test leads (stratified 75/25 split).")

        eval_rows = []
        for m_name, m_data in models.items():
            eval_rows.append({
                "Algorithm": m_name,
                "Accuracy": f"{m_data['accuracy']:.3f}",
                "Precision": f"{m_data['precision']:.3f}",
                "Recall": f"{m_data['recall']:.3f}",
                "F1-Score": f"{m_data['f1']:.3f}",
                "ROC-AUC": f"{m_data['roc_auc']:.3f}",
            })
        st.dataframe(pd.DataFrame(eval_rows), use_container_width=True, hide_index=True)

        # ROC Curve & Feature Importance
        ml_col1, ml_col2 = st.columns(2)

        with ml_col1:
            st.subheader("ROC-AUC Curves")
            roc_fig = go.Figure()
            for m_name, m_data in models.items():
                roc_fig.add_trace(go.Scatter(
                    x=m_data["fpr"], y=m_data["tpr"],
                    name=f"{m_name} (AUC: {m_data['roc_auc']:.2f})",
                    mode="lines"
                ))
            roc_fig.add_trace(go.Scatter(x=[0, 1], y=[0, 1], name="Random Baseline", line=dict(dash="dash", color="gray")))
            roc_fig.update_layout(
                xaxis_title="False Positive Rate",
                yaxis_title="True Positive Rate (Recall)",
                margin=dict(l=10, r=10, t=30, b=10)
            )
            st.plotly_chart(roc_fig, use_container_width=True)

        with ml_col2:
            st.subheader("Top Predictive Feature Importances")
            feat_df = ml_results["feature_importance"].head(10)
            feat_fig = px.bar(
                feat_df, x="importance", y="feature",
                orientation="h",
                color="importance",
                color_continuous_scale="Blues"
            )
            feat_fig.update_layout(yaxis=dict(autorange="reversed"), margin=dict(l=10, r=10, t=30, b=10))
            st.plotly_chart(feat_fig, use_container_width=True)

        st.markdown("---")

        # Lead Risk Segmentation
        st.subheader("Portfolio Lead Conversion Tiers")
        scored_leads = ml_results["scored_leads"]
        tier_counts = scored_leads["conversion_tier"].value_counts().reset_index()
        tier_counts.columns = ["Conversion Tier", "Number of Leads"]

        t_col1, t_col2 = st.columns([1, 1])
        with t_col1:
            tier_fig = px.pie(
                tier_counts, names="Conversion Tier", values="Number of Leads",
                color="Conversion Tier",
                color_discrete_map={
                    "High (>65%)": "#10B981",
                    "Medium (35-65%)": "#F59E0B",
                    "Low (<35%)": "#EF4444"
                },
                hole=0.4
            )
            st.plotly_chart(tier_fig, use_container_width=True)

        with t_col2:
            st.markdown("#### Strategic Routing Recommendations")
            st.markdown("""
            - 🟢 **High Tier (>65% Win Probability):** Fast-track directly to senior Account Executives. Mandate SLA outreach within **< 1 hour**.
            - 🟡 **Medium Tier (35-65%):** Enroll in personalized multi-touch marketing email sequence and SDR follow-up within 12 hours.
            - 🔴 **Low Tier (<35%):** Automated digital nurturing only. Do **NOT** assign manual SDR calling capacity until prospect demonstrates re-engagement.
            """)

        st.markdown("---")

        # Interactive Lead Scorer Tool
        st.subheader("🎯 Interactive Lead Scorer (Real-Time Predictive Tool)")
        st.markdown("Input lead profile attributes below to calculate instant conversion probability and receive algorithmic routing guidance.")

        with st.form("single_lead_scorer_form"):
            form_c1, form_c2, form_c3 = st.columns(3)
            with form_c1:
                in_score = st.slider("Lead Score (0 - 100)", 10, 100, 75)
                in_channel = st.selectbox("Marketing Channel", options=all_channels if all_channels else ["Google Ads", "Meta Ads", "LinkedIn Ads"])
                in_industry = st.selectbox("Industry", options=all_industries if all_industries else ["Technology & SaaS", "Healthcare", "Financial Services"])
            with form_c2:
                in_size = st.selectbox("Company Size", ["1-10", "11-50", "51-200", "201-500", "500+"])
                in_followup = st.slider("Follow-Up Response Time (Hours)", 0.5, 72.0, 3.0, step=0.5)
                in_interactions = st.slider("Number of Digital Interactions", 1, 12, 4)
            with form_c3:
                in_qual = st.selectbox("Qualification Status", ["Unqualified", "MQL", "SQL"], index=1)
                in_eng = st.selectbox("Engagement Level", ["Low", "Medium", "High"], index=1)
                in_camp = st.selectbox("Campaign ID", options=campaign_options[:5] if campaign_options else ["CMP-001"])

            submit_score = st.form_submit_button("⚡ Predict Lead Conversion Probability")

        if submit_score:
            single_lead_dict = {
                "lead_score": in_score,
                "follow_up_time_hours": in_followup,
                "num_interactions": in_interactions,
                "lead_source": in_channel,
                "campaign_id": in_camp,
                "industry": in_industry,
                "company_size": in_size,
                "engagement_level": in_eng,
                "qualification_status": in_qual
            }

            best_pipe = models[best_model]["pipeline"]
            prob, tier, action = predict_single_lead(best_pipe, single_lead_dict)

            res_c1, res_c2 = st.columns([1, 2])
            with res_c1:
                st.metric("Predicted Conversion Probability", f"{prob*100:.1f}%")
                st.markdown(f"**Assigned Tier:** `{tier}`")
            with res_c2:
                if tier == "High":
                    st.success(f"**Recommended Action:** {action}")
                elif tier == "Medium":
                    st.warning(f"**Recommended Action:** {action}")
                else:
                    st.error(f"**Recommended Action:** {action}")


# ==============================================================================
# PAGE 6: AI INSIGHTS & REVENUE LEAKAGE
# ==============================================================================
elif selected_page == "6. AI Insights & Leakage":
    st.title("💡 AI-Powered Revenue Leakage Detection")
    st.markdown('<div class="subtext">Algorithmic diagnosis of funnel drop-offs, capital misallocation, and evidence-backed marketing optimization roadmap.</div>', unsafe_allow_html=True)

    # Top Status Row
    l_c1, l_c2, l_c3 = st.columns(3)
    with l_c1:
        st.metric("Detected Revenue Leakages", len(leakage_issues))
    with l_c2:
        high_leaks = len([i for i in leakage_issues if i.get("priority") == "High"])
        st.metric("High-Priority Critical Issues", high_leaks)
    with l_c3:
        st.metric("Strategic Action Directives", len(action_plan))

    st.markdown("---")

    # Executive Narrative Section
    st.subheader("📑 Executive Strategic Diagnostic Briefing")
    exec_brief = generate_executive_narrative(kpis, leakage_issues, action_plan, st.session_state.openai_api_key)
    st.info(f"**Synthesized via:** `{exec_brief['engine']}`")
    st.markdown(exec_brief["executive_summary"])

    st.markdown("---")

    # Detailed Detected Leakages
    st.subheader("🔍 Diagnosed Funnel & Marketing Leakages")
    for issue in leakage_issues:
        priority = issue.get("priority", "Medium")
        badge_cls = "badge-high" if priority == "High" else ("badge-med" if priority == "Medium" else "badge-low")

        with st.expander(f"[{priority.upper()}] {issue.get('problem')}", expanded=(priority == "High")):
            st.markdown(f"<span class='{badge_cls}'>{priority} Priority</span> • **Category:** {issue.get('category')}", unsafe_allow_html=True)
            st.markdown(f"• **Empirical Evidence:** {issue.get('evidence')}")
            st.markdown(f"• **Contributing Factors:** {issue.get('contributing_factors')}")
            st.markdown(f"• **Business Impact:** {issue.get('business_impact')}")
            st.markdown(f"• **Recommended Remediation:** **{issue.get('recommendation')}**")
            st.markdown(f"• **KPI to Monitor:** `{issue.get('kpi_to_monitor')}`")

    st.markdown("---")

    # Prioritized Action Roadmap
    st.subheader("📅 Prioritized 30/60/90-Day Marketing Action Plan")
    plan_df = pd.DataFrame(action_plan)
    if not plan_df.empty:
        st.dataframe(plan_df, use_container_width=True, hide_index=True)

    st.markdown("---")

    # PDF Report Download
    st.subheader("📄 C-Suite Management Report Export")
    st.markdown("Generate and download a comprehensive, publication-grade executive PDF briefing containing all KPIs, funnel audits, attribution comparisons, and action plans.")

    if st.button("📥 Generate & Download Management PDF Report", type="primary"):
        with st.spinner("Compiling ReportLab executive briefing PDF..."):
            pdf_buffer = generate_executive_pdf_report(
                kpis=kpis,
                funnel_data=funnel_data,
                attribution_data=attribution_linear,
                campaign_data=campaign_metrics_df,
                ml_results={},
                leakage_issues=leakage_issues,
                action_plan=action_plan,
                executive_narrative=exec_brief["executive_summary"]
            )
            st.download_button(
                label="⬇️ Click Here to Download PDF Report",
                data=pdf_buffer.getvalue(),
                file_name=f"RevenueLens_Executive_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf"
            )


# ==============================================================================
# PAGE 7: SCENARIO SIMULATOR
# ==============================================================================
elif selected_page == "7. Scenario Simulator":
    st.title("🎛️ Revenue Opportunity & Scenario Simulator")
    st.markdown('<div class="subtext">What-If forecasting tool to project the revenue, CAC, and ROAS impact of budget reallocations and conversion enhancements.</div>', unsafe_allow_html=True)

    # Simulator Levers in Columns
    st.markdown("### ⚙️ Managerial Decision Levers")
    s_c1, s_c2, s_c3 = st.columns(3)

    with s_c1:
        sim_budget_scale = st.slider("Total Marketing Budget Scale (%)", -40, 100, 15, step=5)
        sim_realloc_boost = st.slider("Budget Reallocation to Top ROAS Channels (%)", 0, 20, 8, step=2)

    with s_c2:
        sim_cpl_delta = st.slider("Cost Per Lead (CPL) Adjustment (%)", -30, 30, -10, step=5)
        sim_mql_rate_delta = st.slider("Lead Qualification (MQL-to-SQL) Boost (%)", -20, 50, 15, step=5)

    with s_c3:
        sim_conv_delta = st.slider("Sales Conversion Rate Boost (%)", -20, 50, 20, step=5)
        sim_deal_delta = st.slider("Average Deal Value (ACV) Expansion (%)", -20, 40, 10, step=5)

    # Run Simulation
    sim_result = simulate_marketing_scenario(
        baseline_kpis=kpis,
        spend_multiplier=(1.0 + sim_budget_scale / 100.0),
        cpl_delta_pct=sim_cpl_delta,
        mql_rate_delta_pct=sim_mql_rate_delta,
        conversion_rate_delta_pct=sim_conv_delta,
        deal_value_delta_pct=sim_deal_delta,
        budget_reallocation_boost=sim_realloc_boost
    )

    st.markdown("---")

    # Simulation Outcome Metrics
    st.markdown("### 🎯 Projected Business Impact (Hypothetical Model)")
    res_c1, res_c2, res_c3, res_c4 = st.columns(4)

    with res_c1:
        st.metric("Projected Attributed Revenue", f"${sim_result['sim_revenue']:,.0f}", f"{sim_result['revenue_growth_pct']:+.1f}%")
    with res_c2:
        st.metric("Projected Customers Acquired", f"{sim_result['sim_customers']:,}", f"{sim_result['sim_customers'] - kpis['customers']:+d}")
    with res_c3:
        st.metric("Projected ROAS", f"{sim_result['sim_roas']:.2f}x", f"{sim_result['sim_roas'] - kpis['roas']:+.2f}x")
    with res_c4:
        st.metric("Net Contribution Margin Delta", f"${sim_result['net_profit_delta']:+,.0f}")

    # Comparative Waterfall / Grouped Bar
    sim_comp_df = sim_result["comparison_table"]
    plot_comp = sim_comp_df[sim_comp_df["Metric"].isin(["Total Marketing Spend ($)", "Attributed Revenue ($)", "Net Contribution Margin ($)"])]

    fig_sim = px.bar(
        plot_comp, x="Metric", y=["Baseline", "Simulated Scenario"],
        barmode="group",
        color_discrete_map={"Baseline": "#94A3B8", "Simulated Scenario": "#10B981"}
    )
    fig_sim.update_layout(margin=dict(l=10, r=10, t=30, b=10))
    st.plotly_chart(fig_sim, use_container_width=True)

    # Detailed Comparison Table
    st.markdown("### 📋 Baseline vs. Scenario Projection Ledger")
    formatted_table = sim_comp_df.copy()
    for idx, row in formatted_table.iterrows():
        fmt = row["Format"]
        if fmt == "currency":
            formatted_table.at[idx, "Baseline"] = f"${row['Baseline']:,.0f}"
            formatted_table.at[idx, "Simulated Scenario"] = f"${row['Simulated Scenario']:,.0f}"
            formatted_table.at[idx, "Absolute Delta"] = f"${row['Absolute Delta']:+,.0f}"
        elif fmt == "percent":
            formatted_table.at[idx, "Baseline"] = f"{row['Baseline']:.2f}%"
            formatted_table.at[idx, "Simulated Scenario"] = f"{row['Simulated Scenario']:.2f}%"
            formatted_table.at[idx, "Absolute Delta"] = f"{row['Absolute Delta']:+.2f}%"
        elif fmt == "multiplier":
            formatted_table.at[idx, "Baseline"] = f"{row['Baseline']:.2f}x"
            formatted_table.at[idx, "Simulated Scenario"] = f"{row['Simulated Scenario']:.2f}x"
            formatted_table.at[idx, "Absolute Delta"] = f"{row['Absolute Delta']:+.2f}x"
        elif fmt == "integer":
            formatted_table.at[idx, "Baseline"] = f"{int(row['Baseline']):,}"
            formatted_table.at[idx, "Simulated Scenario"] = f"{int(row['Simulated Scenario']):,}"
            formatted_table.at[idx, "Absolute Delta"] = f"{int(row['Absolute Delta']):+d}"

    formatted_table["Percentage Change (%)"] = formatted_table["Percentage Change (%)"].apply(lambda x: f"{x:+.1f}%")
    st.dataframe(formatted_table.drop(columns=["Format"]), use_container_width=True, hide_index=True)


# ==============================================================================
# PAGE 8: DATA MANAGEMENT & UPLOAD
# ==============================================================================
elif selected_page == "8. Data Management & Upload":
    st.title("💾 Data Management, Upload & Validation")
    st.markdown('<div class="subtext">Upload custom datasets, inspect schema integrity, manage SQLite database, and download data templates.</div>', unsafe_allow_html=True)

    tab_upload, tab_db, tab_templates = st.tabs(["📤 Upload Datasets", "🗄️ SQLite Database Browser", "📄 Download Templates"])

    with tab_upload:
        st.subheader("Upload Custom Marketing & Sales Datasets")
        st.caption("Upload CSV or Excel files. Missing columns will be flagged with actionable validation feedback.")

        up_col1, up_col2 = st.columns(2)
        with up_col1:
            camp_file = st.file_uploader("Upload Campaigns Dataset", type=["csv", "xlsx"])
            lead_file = st.file_uploader("Upload Leads Dataset", type=["csv", "xlsx"])
        with up_col2:
            journey_file = st.file_uploader("Upload Customer Journey Dataset", type=["csv", "xlsx"])
            sales_file = st.file_uploader("Upload Sales Dataset", type=["csv", "xlsx"])

        if st.button("Process & Validate Uploaded Files"):
            def read_file(f):
                if f is None:
                    return None
                if f.name.endswith(".csv"):
                    return pd.read_csv(f)
                else:
                    return pd.read_excel(f)

            u_camp = read_file(camp_file)
            u_lead = read_file(lead_file)
            u_jour = read_file(journey_file)
            u_sale = read_file(sales_file)

            val_report = validate_datasets(u_camp, u_lead, u_jour, u_sale)

            if val_report["is_valid"]:
                st.success("✅ **Validation Passed:** Uploaded datasets satisfy all schema and data integrity requirements.")
                # Save to session and SQLite
                save_to_sqlite(
                    u_camp if u_camp is not None else st.session_state.datasets["campaigns"],
                    u_lead if u_lead is not None else st.session_state.datasets["leads"],
                    u_jour if u_jour is not None else st.session_state.datasets["customer_journey"],
                    u_sale if u_sale is not None else st.session_state.datasets["sales"],
                )
                st.session_state.datasets = load_data_from_db()
                st.rerun()
            else:
                st.error("❌ **Validation Failed:** Please resolve the errors below before loading data.")
                for err in val_report["errors"]:
                    st.write(f"• 🚨 {err}")

            if val_report["warnings"]:
                st.warning("⚠️ **Data Warnings & Non-Critical Discrepancies:**")
                for w in val_report["warnings"]:
                    st.write(f"• {w}")

    with tab_db:
        st.subheader("Current SQLite Database Records")
        tbl_choice = st.selectbox("Select Table to Preview:", ["campaigns", "leads", "customer_journey", "sales"])
        curr_df = st.session_state.datasets.get(tbl_choice, pd.DataFrame())
        st.caption(f"Table `{tbl_choice}` contains **{len(curr_df):,}** records.")
        st.dataframe(curr_df.head(100), use_container_width=True)

        if st.button("🔄 Reset Database to Synthetic Sample Benchmark"):
            with st.spinner("Regenerating synthetic benchmark dataset..."):
                st.session_state.datasets = generate_synthetic_data(seed=42)
                st.success("Database reset to benchmark synthetic dataset.")
                st.rerun()

    with tab_templates:
        st.subheader("Download Standard Clean Data Templates")
        st.markdown("Download pre-formatted CSV and Excel templates with proper column headers and sample records.")

        t_c1, t_c2 = st.columns(2)
        with t_c1:
            for fname in ["campaigns_template.csv", "leads_template.csv"]:
                p = os.path.join(TEMPLATES_DIR, fname)
                if os.path.exists(p):
                    with open(p, "rb") as f:
                        st.download_button(f"📥 Download {fname}", data=f.read(), file_name=fname, mime="text/csv")
        with t_c2:
            for fname in ["customer_journey_template.csv", "sales_template.csv"]:
                p = os.path.join(TEMPLATES_DIR, fname)
                if os.path.exists(p):
                    with open(p, "rb") as f:
                        st.download_button(f"📥 Download {fname}", data=f.read(), file_name=fname, mime="text/csv")


# ==============================================================================
# PAGE 9: METHODOLOGY & DEFINITIONS
# ==============================================================================
elif selected_page == "9. Methodology & Definitions":
    st.title("📖 Methodology, Formulas & Academic Frameworks")
    st.markdown('<div class="subtext">Documented mathematical definitions, attribution models, ML caveats, and data science integrity standards.</div>', unsafe_allow_html=True)

    with st.expander("📐 Core Marketing & Revenue Formulas", expanded=True):
        st.markdown("""
        - **Click-Through Rate (CTR):**
          $$\\text{CTR} = \\frac{\\text{Total Clicks}}{\\text{Impressions}} \\times 100$$
        - **Cost Per Lead (CPL):**
          $$\\text{CPL} = \\frac{\\text{Marketing Spend}}{\\text{Total Leads Generated}}$$
        - **Customer Acquisition Cost (CAC):**
          $$\\text{CAC} = \\frac{\\text{Total Marketing Spend}}{\\text{Closed-Won Customers}}$$
        - **Lead-to-Customer Conversion Rate:**
          $$\\text{Conversion Rate (\\%)} = \\frac{\\text{Closed-Won Customers}}{\\text{Eligible Leads}} \\times 100$$
        - **Return on Ad Spend (ROAS):**
          $$\\text{ROAS} = \\frac{\\text{Attributed Revenue}}{\\text{Marketing Spend}}$$
        - **Marketing ROI (\\%):**
          $$\\text{Marketing ROI} = \\frac{\\text{Attributed Revenue} - \\text{Marketing Spend}}{\\text{Marketing Spend}} \\times 100$$
          *(Attributed revenue serves as a revenue-based proxy in the absence of COGS/gross margin data).*
        """)

    with st.expander("⚖️ Multi-Touch Attribution Models"):
        st.markdown("""
        1. **First-Touch Attribution:**
           Assigns 100% of revenue credit to the initial touchpoint. Highlights brand awareness and top-of-funnel discovery channels.
        2. **Last-Touch Attribution:**
           Assigns 100% of credit to the final recorded marketing touchpoint before opportunity creation. Favors conversion-focused bottom-funnel tactics.
        3. **Linear Attribution:**
           Splits credit equally ($1/N$) across all $N$ interactions in the buyer's journey.
        4. **Position-Based (U-Shaped) Attribution:**
           Awards **40%** credit to the first touch, **40%** to the final conversion touch, and distributes the remaining **20%** equally across intermediary nurturing touches.
        5. **Time-Decay Attribution:**
           Applies exponential half-life decay:
           $$w_i = 2^{-\\frac{\\Delta t_i}{\\lambda}}$$
           Touchpoints occurring closer to the deal close receive exponentially greater weight ($\lambda = 7\\text{ days}$).
        """)

    with st.expander("🤖 Machine Learning & Data Leakage Prevention"):
        st.markdown("""
        - **Leakage Prevention:** Features are strictly limited to attributes known at the time of lead capture (e.g., source, initial score, firmographics, response time). Pipeline outcomes (`sales_stage`, `close_date`, `revenue`) are strictly excluded from predictive feature matrices.
        - **Algorithms:** Evaluates both **Logistic Regression** (for interpretable odds ratios) and **Random Forest** (to capture non-linear interaction effects).
        - **Predictive vs. Causal:** Machine learning identifies statistical associations. While rapid follow-up correlates strongly with higher conversion, incrementality tests (A/B testing) are recommended to prove strict causality.
        """)

    with st.expander("⚠️ Analytical & Synthetic Data Disclaimers"):
        st.markdown("""
        - **Benchmarking Notice:** Synthetic datasets are generated under fixed seeds to realistically emulate marketing problems (e.g., vanity lead bloat in Meta ads vs. high-intent conversions in Google Search).
        - **Revenue Allocation:** Total attributed revenue across channels is mathematically bounded to never exceed actual recognized revenue.
        """)
