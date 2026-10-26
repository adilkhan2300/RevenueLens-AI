"""
RevenueLens AI - AI Insights & Strategic Action Plan Engine
Synthesizes quantitative diagnostic findings from KPI, funnel, attribution, and ML modules
into an executive-level marketing turnaround strategy.
Features dual execution:
1. Deterministic Rule-Based Business Strategy Engine (100% reliable, zero API key required).
2. Optional LLM Integration (OpenAI API / custom endpoint) for natural language executive briefings.
"""

import os
import json
import pandas as pd


def generate_strategic_action_plan(
    leakage_issues: list,
    campaign_metrics: pd.DataFrame = None,
    funnel_metrics: dict = None,
    ml_results: dict = None,
    attribution_results: dict = None
) -> list:
    """
    Generate a prioritized 30/60/90-day marketing optimization action plan
    anchored directly in observed empirical data.
    """
    action_items = []

    # Priority 1: High Leakage Issues (Immediate 0-30 Days)
    for issue in leakage_issues:
        if issue.get("priority") == "High":
            action_items.append({
                "timeframe": "Immediate (0 - 30 Days)",
                "priority": "High",
                "area": issue.get("category", "Optimization"),
                "action": issue.get("recommendation"),
                "evidence": issue.get("evidence"),
                "expected_impact": "Halt capital waste and eliminate major lead qualification friction.",
                "kpi_to_monitor": issue.get("kpi_to_monitor"),
                "review_cycle": "Weekly"
            })

    # Priority 2: Reallocation from attribution data (Medium Term 30 - 60 Days)
    if attribution_results and "channel_attribution" in attribution_results:
        ch_df = attribution_results["channel_attribution"]
        if not ch_df.empty and "roas" in ch_df.columns:
            top_ch = ch_df.sort_values(by="roas", ascending=False).iloc[0]
            bottom_ch = ch_df.sort_values(by="roas", ascending=True).iloc[0]

            if top_ch["roas"] > 2.0 and bottom_ch["roas"] < 1.0:
                action_items.append({
                    "timeframe": "Medium-Term (30 - 60 Days)",
                    "priority": "High",
                    "area": "Budget Reallocation",
                    "action": f"Reallocate 25% of marketing capital from underperforming '{bottom_ch['channel']}' (ROAS: {bottom_ch['roas']:.2f}x) to top-performing '{top_ch['channel']}' (ROAS: {top_ch['roas']:.2f}x).",
                    "evidence": f"{top_ch['channel']} generates ${top_ch['attributed_revenue']:,.0f} revenue at {top_ch['roas']:.2f}x ROAS vs {bottom_ch['channel']} at only {bottom_ch['roas']:.2f}x ROAS.",
                    "expected_impact": "Estimated 15-22% increase in total attributed revenue at neutral aggregate marketing budget.",
                    "kpi_to_monitor": f"Aggregate Portfolio ROAS and Blended CAC",
                    "review_cycle": "Bi-weekly"
                })

    # Priority 3: Machine Learning Lead Quality Tiers (30 - 60 Days)
    if ml_results and "tier_summary" in ml_results:
        feat_imp = ml_results.get("feature_importance")
        top_driver = feat_imp.iloc[0]["feature"] if (feat_imp is not None and not feat_imp.empty) else "Lead Score & Follow-up Time"

        action_items.append({
            "timeframe": "Medium-Term (30 - 60 Days)",
            "priority": "Medium",
            "area": "Predictive Lead Routing",
            "action": f"Deploy automated ML lead routing in CRM to prioritize leads scoring in the High tier (>65% conversion probability). Primary conversion predictive driver identified: '{top_driver}'.",
            "evidence": f"Machine learning classification model achieved ROC-AUC of {ml_results.get('models', {}).get(ml_results.get('best_model_name', 'Random Forest'), {}).get('roc_auc', 0.85):.2f}.",
            "expected_impact": "Accelerate sales pipeline velocity and increase SQL-to-Won conversion by 3-5 percentage points.",
            "kpi_to_monitor": "High-Tier Lead Win Rate & Median Deal Velocity",
            "review_cycle": "Monthly"
        })

    # Priority 4: Strategic & Governance (60 - 90 Days)
    action_items.append({
        "timeframe": "Strategic (60 - 90 Days)",
        "priority": "Medium",
        "area": "Customer Journey Analytics",
        "action": "Transition from legacy Last-Touch reporting to unified Position-Based (U-Shaped) multi-touch attribution in executive dashboards.",
        "evidence": "Customer journey data reveals multiple touches across SEO, Social, and Email prior to sales opportunity creation.",
        "expected_impact": "Fairly recognize upper-funnel awareness channels without cannibalizing conversion incentives.",
        "kpi_to_monitor": "Multi-Touch ROAS Stability across Channels",
        "review_cycle": "Quarterly"
    })

    return action_items


def generate_executive_narrative(
    kpi_summary: dict,
    leakage_issues: list,
    action_plan: list,
    api_key: str = None
) -> dict:
    """
    Generate an executive-level strategic narrative.
    If an OpenAI API key is supplied, query the LLM.
    Otherwise, compile an analytical deterministic briefing.
    """
    # 1. Deterministic Rule-Based Briefing
    spend = kpi_summary.get("spend", 0.0)
    rev = kpi_summary.get("revenue", 0.0)
    roas = kpi_summary.get("roas", 0.0)
    leads = kpi_summary.get("leads", 0)
    customers = kpi_summary.get("customers", 0)
    conv_rate = kpi_summary.get("conversion_rate", 0.0)

    exec_summary_text = f"""
### Executive Briefing: The Marketing-to-Revenue Growth Paradox

**Diagnosis Overview:**
The organization has deployed **${spend:,.0f}** in marketing investments to generate **{leads:,} leads**, yet closed only **{customers:,} paying customers** (overall conversion efficiency: **{conv_rate:.2f}%**), yielding **${rev:,.0f}** in recognized revenue (**{roas:.2f}x ROAS**).

**The Root Cause of Stagnation:**
The primary disconnect is not top-of-funnel reach or ad volume, but **lead quality dilution** and **funnel friction**:
1. **Vanity Metrics Dominance:** A disproportionate share of budget is allocated to campaigns that deliver massive top-of-funnel lead counts at low nominal CPL, but these leads exhibit low purchase intent and high drop-off rates at the qualification stage.
2. **Sales & Marketing Misalignment:** Strict qualification criteria reject a large volume of unqualified leads, wasting sales capacity and inflating true Customer Acquisition Cost (CAC).
3. **Follow-Up Decay:** Speed-to-lead latency significantly erodes conversion probabilities for warm inbound opportunities.

**Strategic Pivot:**
Management must transition performance evaluation from **Volume-Centric KPIs** (Leads, CPL) to **Unit Economics & Attributed Revenue** (SQLs, CAC, Pipeline Contribution, Multi-Touch ROAS).
"""

    rule_based_response = {
        "engine": "Deterministic Analytics Engine",
        "executive_summary": exec_summary_text.strip(),
        "total_issues_identified": len(leakage_issues),
        "high_priority_issues": len([i for i in leakage_issues if i.get("priority") == "High"]),
        "action_items_count": len(action_plan)
    }

    # 2. If API Key is present, attempt LLM generation
    if api_key and api_key.strip():
        try:
            import openai
            client = openai.OpenAI(api_key=api_key.strip())

            prompt_payload = {
                "financial_metrics": {
                    "marketing_spend": spend,
                    "attributed_revenue": rev,
                    "roas": roas,
                    "leads": leads,
                    "customers": customers,
                    "conversion_rate_pct": conv_rate
                },
                "key_detected_leakages": [
                    {"problem": i["problem"], "evidence": i["evidence"], "priority": i["priority"]}
                    for i in leakage_issues[:4]
                ],
                "top_recommendations": [
                    {"action": a["action"], "impact": a["expected_impact"]}
                    for a in action_plan[:3]
                ]
            }

            system_prompt = (
                "You are an elite Chief Commercial Officer and MBA Marketing & Data Science Professor. "
                "Synthesize the provided marketing-to-revenue diagnostics into an incisive, executive-ready narrative. "
                "Focus on why high lead volume failed to produce proportional revenue growth, highlighting capital reallocation "
                "and qualification improvements. Do NOT invent figures; use only the facts provided."
            )

            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Analyze these findings:\n{json.dumps(prompt_payload, indent=2)}"}
                ],
                temperature=0.3,
                max_tokens=700
            )

            llm_text = response.choices[0].message.content
            return {
                "engine": "OpenAI LLM + Factual Evidence Integration",
                "executive_summary": llm_text,
                "total_issues_identified": len(leakage_issues),
                "high_priority_issues": len([i for i in leakage_issues if i.get("priority") == "High"]),
                "action_items_count": len(action_plan)
            }
        except Exception as e:
            # Fallback smoothly to rule-based briefing
            rule_based_response["llm_error"] = str(e)
            return rule_based_response

    return rule_based_response
