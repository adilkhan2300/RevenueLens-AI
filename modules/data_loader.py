"""
RevenueLens AI - Data Loader & Validation Module
Handles synthetic dataset generation, CSV/Excel loading, validation,
referential integrity verification, and SQLite persistence.
"""

import os
import sqlite3
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
SAMPLE_DIR = os.path.join(DATA_DIR, "sample")
TEMPLATES_DIR = os.path.join(DATA_DIR, "templates")
DB_PATH = os.path.join(DATA_DIR, "database.db")


def ensure_directories():
    """Ensure all required directories exist."""
    for directory in [DATA_DIR, SAMPLE_DIR, TEMPLATES_DIR]:
        os.makedirs(directory, exist_ok=True)


def generate_synthetic_data(seed: int = 42) -> dict:
    """
    Generate realistic, business-grounded synthetic marketing datasets.
    Includes intentional patterns:
    - Campaign 1 (Meta Lead Gen): high leads, low score, high drop-off (Vanity Trap).
    - Campaign 2 (Google Search BOFU): high CPL, high conversion, high revenue (Hidden Gem).
    - Campaign 3 (LinkedIn Enterprise): high CAC, large deals, long cycle.
    - Campaign 4 (Email Nurturing): low cost, high ROI.
    - Follow-up time correlation: <4h follow-up -> much higher conversion.
    """
    ensure_directories()
    np.random.seed(seed)

    base_date = datetime(2025, 1, 1)

    # 1. CAMPAIGNS (14 campaigns across 7 channels)
    campaigns_data = [
        # id, name, channel, objective, start_offset, duration_days, impr, clicks, spend
        ("CMP-001", "Google Search - High Intent BOFU", "Google Ads", "Conversion", 0, 180, 145000, 11600, 29000.0),
        ("CMP-002", "Google Display - Remarketing", "Google Ads", "Retargeting", 15, 165, 320000, 6400, 12800.0),
        ("CMP-003", "Meta - Broad Lead Gen Form", "Meta Ads", "Lead Generation", 0, 180, 850000, 25500, 38250.0),
        ("CMP-004", "Meta - Video Testimonials", "Meta Ads", "Awareness", 30, 150, 420000, 8400, 16800.0),
        ("CMP-005", "LinkedIn - Enterprise Decision Makers", "LinkedIn Ads", "Lead Generation", 0, 180, 95000, 3800, 34200.0),
        ("CMP-006", "LinkedIn - Sponsored Thought Leadership", "LinkedIn Ads", "Engagement", 45, 135, 130000, 3900, 19500.0),
        ("CMP-007", "Email - Product Launch Sequence", "Email Marketing", "Conversion", 10, 170, 65000, 9750, 4800.0),
        ("CMP-008", "Email - Re-engagement Campaign", "Email Marketing", "Retention", 60, 120, 48000, 4800, 2400.0),
        ("CMP-009", "Organic Search - Solution Pillar Pages", "Organic Search", "Inbound", 0, 180, 280000, 14000, 12000.0),
        ("CMP-010", "Organic Search - High Ranking Comparison", "Organic Search", "Inbound", 0, 180, 190000, 11400, 8500.0),
        ("CMP-011", "Content - Industry Benchmark Report", "Content Marketing", "Lead Generation", 20, 160, 160000, 8000, 11200.0),
        ("CMP-012", "Content - Technical Whitepaper Series", "Content Marketing", "Lead Generation", 40, 140, 110000, 4400, 8800.0),
        ("CMP-013", "Referral - Agency Partner Program", "Referral", "Partner", 0, 180, 35000, 3150, 15750.0),
        ("CMP-014", "Referral - Customer Advocate Rewards", "Referral", "Advocacy", 30, 150, 22000, 2200, 6600.0),
    ]

    campaign_rows = []
    for c_id, name, ch, obj, s_off, dur, impr, clk, spd in campaigns_data:
        s_date = base_date + timedelta(days=s_off)
        e_date = s_date + timedelta(days=dur)
        campaign_rows.append({
            "campaign_id": c_id,
            "campaign_name": name,
            "channel": ch,
            "campaign_objective": obj,
            "start_date": s_date.strftime("%Y-%m-%d"),
            "end_date": e_date.strftime("%Y-%m-%d"),
            "impressions": int(impr),
            "clicks": int(clk),
            "spend": float(spd),
        })

    campaigns_df = pd.DataFrame(campaign_rows)

    # 2. LEADS GENERATION (approx 1,800 leads)
    # Target distribution of leads per campaign reflecting real marketing behavior
    campaign_lead_weights = {
        "CMP-001": 260,  # High intent Google
        "CMP-002": 110,  # Retargeting
        "CMP-003": 580,  # Meta Broad - huge lead bloat!
        "CMP-004": 120,  # Meta Video
        "CMP-005": 95,   # LinkedIn Enterprise
        "CMP-006": 65,   # LinkedIn Thought Leadership
        "CMP-007": 190,  # Email Launch
        "CMP-008": 70,   # Email Re-engage
        "CMP-009": 140,  # Organic Pillar
        "CMP-010": 115,  # Organic Comparison
        "CMP-011": 130,  # Content Benchmark
        "CMP-012": 60,   # Content Whitepaper
        "CMP-013": 85,   # Referral Agency
        "CMP-014": 55,   # Referral Customer
    }

    industries = ["Technology & SaaS", "Healthcare", "Financial Services", "E-Commerce & Retail", "Manufacturing", "Professional Services"]
    industry_probs = [0.35, 0.18, 0.17, 0.15, 0.08, 0.07]
    company_sizes = ["1-10", "11-50", "51-200", "201-500", "500+"]
    company_size_probs = [0.30, 0.35, 0.20, 0.10, 0.05]

    lead_rows = []
    journey_rows = []
    sales_rows = []

    lead_counter = 1
    cust_counter = 1
    opp_counter = 1

    for c_id, count in campaign_lead_weights.items():
        camp_meta = next(c for c in campaign_rows if c["campaign_id"] == c_id)
        c_start = datetime.strptime(camp_meta["start_date"], "%Y-%m-%d")
        c_dur = (datetime.strptime(camp_meta["end_date"], "%Y-%m-%d") - c_start).days

        for _ in range(count):
            lead_id = f"LED-{lead_counter:05d}"
            customer_id = f"CUST-{cust_counter:05d}"
            lead_counter += 1
            cust_counter += 1

            # Lead Date within campaign duration
            lead_day_offset = int(np.random.beta(2, 3) * c_dur)
            lead_date = c_start + timedelta(days=lead_day_offset)

            # Industry and company size
            ind = np.random.choice(industries, p=industry_probs)
            c_size = np.random.choice(company_sizes, p=company_size_probs)

            # Specific dynamics per campaign
            if c_id == "CMP-003":  # Meta Broad - low quality leads
                lead_score = int(np.clip(np.random.normal(38, 14), 10, 85))
                follow_up = float(np.round(np.random.exponential(36) + 12, 1))  # Slower follow-up due to high volume
                interactions = int(np.random.poisson(1.8) + 1)
            elif c_id in ["CMP-001", "CMP-013"]:  # Google BOFU or Referral - high quality
                lead_score = int(np.clip(np.random.normal(78, 12), 35, 99))
                follow_up = float(np.round(np.random.exponential(4) + 0.8, 1))  # Rapid follow-up
                interactions = int(np.random.poisson(4.5) + 2)
            elif c_id in ["CMP-005", "CMP-006"]:  # LinkedIn B2B Enterprise
                lead_score = int(np.clip(np.random.normal(72, 14), 30, 98))
                follow_up = float(np.round(np.random.exponential(12) + 2, 1))
                interactions = int(np.random.poisson(5.0) + 2)
            elif c_id in ["CMP-007", "CMP-008"]:  # Email
                lead_score = int(np.clip(np.random.normal(68, 15), 25, 95))
                follow_up = float(np.round(np.random.exponential(8) + 1.5, 1))
                interactions = int(np.random.poisson(3.8) + 2)
            else:
                lead_score = int(np.clip(np.random.normal(55, 16), 15, 92))
                follow_up = float(np.round(np.random.exponential(18) + 2, 1))
                interactions = int(np.random.poisson(2.8) + 1)

            # Qualification status based on score
            if lead_score < 45:
                qual_status = "Unqualified"
            elif lead_score < 70:
                qual_status = "MQL"
            else:
                qual_status = "SQL"

            # Probability of converting to opportunity and deal
            # Influenced by: lead_score, follow_up_time (fast is better), industry, interactions
            conversion_logit = -2.8 + (lead_score / 25.0) - (follow_up / 35.0) + (interactions * 0.25)
            if c_size in ["201-500", "500+"]:
                conversion_logit += 0.4
            if qual_status == "Unqualified":
                conversion_logit -= 2.5
            elif qual_status == "SQL":
                conversion_logit += 0.8

            prob_convert = 1.0 / (1.0 + np.exp(-conversion_logit))
            is_converted = int(np.random.rand() < prob_convert)

            lead_rows.append({
                "lead_id": lead_id,
                "customer_id": customer_id,
                "campaign_id": c_id,
                "lead_date": lead_date.strftime("%Y-%m-%d"),
                "lead_source": camp_meta["channel"],
                "lead_score": lead_score,
                "qualification_status": qual_status,
                "industry": ind,
                "company_size": c_size,
                "follow_up_time_hours": follow_up,
                "engagement_level": "High" if interactions >= 5 else ("Medium" if interactions >= 3 else "Low"),
                "num_interactions": interactions,
                "is_converted": is_converted
            })

            # 3. CUSTOMER JOURNEY TOUCHPOINTS (Multi-touch paths)
            # Create 1 to 5 touchpoints per lead
            num_touches = 1 if is_converted == 0 and np.random.rand() > 0.4 else int(np.random.choice([1, 2, 3, 4, 5], p=[0.25, 0.35, 0.22, 0.12, 0.06]))
            # Lead's primary campaign is either the first or middle touch
            journey_camps = [c_id]
            if num_touches > 1:
                other_camps = [c["campaign_id"] for c in campaign_rows if c["campaign_id"] != c_id]
                additional = list(np.random.choice(other_camps, size=num_touches - 1, replace=True))
                journey_camps.extend(additional)
                # Shuffle order so primary campaign could be first, middle, or last
                np.random.shuffle(journey_camps)

            touch_types = ["Impression", "Ad Click", "Website Visit", "Content Download", "Webinar Attendance", "Product Demo", "Sales Call"]
            start_touch_time = lead_date - timedelta(days=int(np.random.randint(2, 28)))

            for t_idx, t_camp_id in enumerate(journey_camps):
                t_camp_meta = next(c for c in campaign_rows if c["campaign_id"] == t_camp_id)
                t_time = start_touch_time + timedelta(days=t_idx * int(np.random.randint(1, 7)) + 1)
                t_type = touch_types[min(t_idx, len(touch_types) - 1)]

                journey_rows.append({
                    "customer_id": customer_id,
                    "touchpoint_timestamp": t_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "campaign_id": t_camp_id,
                    "channel": t_camp_meta["channel"],
                    "touchpoint_type": t_type,
                })

            # 4. SALES OPPORTUNITIES & REVENUE
            # If converted, lead becomes an opportunity and either Closed-Won or Closed-Lost
            if qual_status in ["MQL", "SQL"] or is_converted == 1:
                opp_id = f"OPP-{opp_counter:05d}"
                opp_counter += 1
                opp_date = lead_date + timedelta(days=int(np.random.randint(1, 10)))

                if is_converted == 1:
                    sales_stage = "Closed-Won"
                    conv_status = "Won"
                    close_date = opp_date + timedelta(days=int(np.random.randint(10, 60)))

                    # Revenue depends on company size and channel
                    if c_size == "500+":
                        rev = float(np.round(np.random.normal(48000, 8000), 2))
                    elif c_size == "201-500":
                        rev = float(np.round(np.random.normal(24000, 4500), 2))
                    elif c_size == "51-200":
                        rev = float(np.round(np.random.normal(12500, 2500), 2))
                    else:
                        rev = float(np.round(np.random.normal(5500, 1200), 2))

                    if camp_meta["channel"] == "LinkedIn Ads":
                        rev *= 1.4  # Enterprise premium
                    rev = max(1500.0, rev)

                else:
                    # Not converted, but had opportunity created
                    sales_stage = np.random.choice(["Closed-Lost", "Negotiation", "Proposal", "Discovery"], p=[0.55, 0.20, 0.15, 0.10])
                    conv_status = "Lost" if sales_stage == "Closed-Lost" else "In Progress"
                    close_date = opp_date + timedelta(days=int(np.random.randint(10, 45))) if sales_stage == "Closed-Lost" else None
                    rev = 0.0

                sales_rows.append({
                    "customer_id": customer_id,
                    "opportunity_id": opp_id,
                    "opportunity_date": opp_date.strftime("%Y-%m-%d"),
                    "sales_stage": sales_stage,
                    "conversion_status": conv_status,
                    "close_date": close_date.strftime("%Y-%m-%d") if close_date else "",
                    "revenue": float(rev),
                })

    leads_df = pd.DataFrame(lead_rows)
    journey_df = pd.DataFrame(journey_rows)
    sales_df = pd.DataFrame(sales_rows)

    # Sort journey by customer and timestamp
    journey_df = journey_df.sort_values(by=["customer_id", "touchpoint_timestamp"]).reset_index(drop=True)

    # Save to CSV in sample directory
    campaigns_df.to_csv(os.path.join(SAMPLE_DIR, "campaigns.csv"), index=False)
    leads_df.to_csv(os.path.join(SAMPLE_DIR, "leads.csv"), index=False)
    journey_df.to_csv(os.path.join(SAMPLE_DIR, "customer_journey.csv"), index=False)
    sales_df.to_csv(os.path.join(SAMPLE_DIR, "sales.csv"), index=False)

    # Also save to SQLite
    save_to_sqlite(campaigns_df, leads_df, journey_df, sales_df)

    # Create empty clean templates
    create_templates()

    return {
        "campaigns": campaigns_df,
        "leads": leads_df,
        "customer_journey": journey_df,
        "sales": sales_df
    }


def save_to_sqlite(campaigns_df: pd.DataFrame, leads_df: pd.DataFrame, journey_df: pd.DataFrame, sales_df: pd.DataFrame):
    """Save cleaned dataframes into SQLite tables."""
    ensure_directories()
    conn = sqlite3.connect(DB_PATH)
    try:
        campaigns_df.to_sql("campaigns", conn, if_exists="replace", index=False)
        leads_df.to_sql("leads", conn, if_exists="replace", index=False)
        journey_df.to_sql("customer_journey", conn, if_exists="replace", index=False)
        sales_df.to_sql("sales", conn, if_exists="replace", index=False)
    finally:
        conn.close()


def load_data_from_db() -> dict:
    """Load data from SQLite database if present, otherwise generate synthetic data."""
    ensure_directories()
    if not os.path.exists(DB_PATH):
        return generate_synthetic_data()

    conn = sqlite3.connect(DB_PATH)
    try:
        campaigns_df = pd.read_sql("SELECT * FROM campaigns", conn)
        leads_df = pd.read_sql("SELECT * FROM leads", conn)
        journey_df = pd.read_sql("SELECT * FROM customer_journey", conn)
        sales_df = pd.read_sql("SELECT * FROM sales", conn)
        return {
            "campaigns": campaigns_df,
            "leads": leads_df,
            "customer_journey": journey_df,
            "sales": sales_df
        }
    except Exception:
        return generate_synthetic_data()
    finally:
        conn.close()


def create_templates():
    """Create downloadable template files with headers and 1 sample row."""
    ensure_directories()
    templates = {
        "campaigns_template.csv": pd.DataFrame([{
            "campaign_id": "CMP-001",
            "campaign_name": "Summer Search Campaign",
            "channel": "Google Ads",
            "campaign_objective": "Conversion",
            "start_date": "2025-01-01",
            "end_date": "2025-06-30",
            "impressions": 100000,
            "clicks": 5000,
            "spend": 12500.00
        }]),
        "leads_template.csv": pd.DataFrame([{
            "lead_id": "LED-00001",
            "customer_id": "CUST-00001",
            "campaign_id": "CMP-001",
            "lead_date": "2025-02-15",
            "lead_source": "Google Ads",
            "lead_score": 75,
            "qualification_status": "SQL",
            "industry": "Technology & SaaS",
            "company_size": "51-200",
            "follow_up_time_hours": 2.5,
            "engagement_level": "High",
            "num_interactions": 4,
            "is_converted": 1
        }]),
        "customer_journey_template.csv": pd.DataFrame([{
            "customer_id": "CUST-00001",
            "touchpoint_timestamp": "2025-02-14 10:30:00",
            "campaign_id": "CMP-001",
            "channel": "Google Ads",
            "touchpoint_type": "Ad Click"
        }]),
        "sales_template.csv": pd.DataFrame([{
            "customer_id": "CUST-00001",
            "opportunity_id": "OPP-00001",
            "opportunity_date": "2025-02-16",
            "sales_stage": "Closed-Won",
            "conversion_status": "Won",
            "close_date": "2025-03-10",
            "revenue": 15000.00
        }])
    }

    for fname, df in templates.items():
        csv_path = os.path.join(TEMPLATES_DIR, fname)
        excel_path = os.path.join(TEMPLATES_DIR, fname.replace(".csv", ".xlsx"))
        df.to_csv(csv_path, index=False)
        try:
            df.to_excel(excel_path, index=False)
        except Exception:
            pass


def validate_datasets(
    campaigns_df: pd.DataFrame = None,
    leads_df: pd.DataFrame = None,
    journey_df: pd.DataFrame = None,
    sales_df: pd.DataFrame = None
) -> dict:
    """
    Validate uploaded or current datasets against requirements:
    - Column presence & mapping
    - Data types & date formatting
    - Duplicate detection
    - Missing value analysis
    - Negative value checks
    - Referential integrity (leads->campaigns, journey->customers, sales->customers)
    Returns:
    {
        "is_valid": bool,
        "errors": list[str],
        "warnings": list[str],
        "info": list[str],
        "unsupported_metrics": list[str],
        "stats": dict
    }
    """
    errors = []
    warnings = []
    info = []
    unsupported_metrics = []
    stats = {}

    # Required and optional columns definition
    expected_cols = {
        "campaigns": {"campaign_id", "channel", "spend"},
        "leads": {"lead_id", "customer_id", "campaign_id"},
        "journey": {"customer_id", "touchpoint_timestamp", "campaign_id"},
        "sales": {"customer_id", "sales_stage", "revenue"}
    }

    # 1. CAMPAIGNS VALIDATION
    if campaigns_df is not None and not campaigns_df.empty:
        c_cols = set(campaigns_df.columns)
        missing_c = expected_cols["campaigns"] - c_cols
        if missing_c:
            errors.append(f"Campaigns dataset missing required columns: {missing_c}")
        else:
            if "spend" in campaigns_df.columns:
                if (campaigns_df["spend"] < 0).any():
                    errors.append("Campaigns contain negative spend values.")
            if campaigns_df["campaign_id"].duplicated().any():
                warnings.append(f"Campaigns contain {campaigns_df['campaign_id'].duplicated().sum()} duplicate campaign IDs.")

            stats["total_campaigns"] = len(campaigns_df)
            stats["total_spend"] = float(campaigns_df["spend"].sum()) if "spend" in campaigns_df.columns else 0.0
    else:
        warnings.append("Campaigns dataset is missing. Channel spend and ROI/ROAS cannot be computed.")
        unsupported_metrics.extend(["Total Marketing Spend", "CPL", "CAC", "ROAS", "Marketing ROI"])

    # 2. LEADS VALIDATION
    if leads_df is not None and not leads_df.empty:
        l_cols = set(leads_df.columns)
        missing_l = expected_cols["leads"] - l_cols
        if missing_l:
            errors.append(f"Leads dataset missing required columns: {missing_l}")
        else:
            if leads_df["lead_id"].duplicated().any():
                warnings.append(f"Leads contain {leads_df['lead_id'].duplicated().sum()} duplicate lead IDs.")

            # Missing value checks
            null_scores = leads_df["lead_score"].isnull().sum() if "lead_score" in leads_df.columns else 0
            if null_scores > 0:
                warnings.append(f"Leads dataset has {null_scores} missing lead scores.")

            stats["total_leads"] = len(leads_df)
            if "qualification_status" in leads_df.columns:
                stats["mql_count"] = int((leads_df["qualification_status"].str.upper() == "MQL").sum())
                stats["sql_count"] = int((leads_df["qualification_status"].str.upper() == "SQL").sum())
    else:
        errors.append("Leads dataset is missing. Lead funnel stages and conversion metrics cannot be computed.")
        unsupported_metrics.extend(["Leads Generated", "MQLs", "SQLs", "Lead-to-Customer Conversion Rate"])

    # 3. SALES VALIDATION
    if sales_df is not None and not sales_df.empty:
        s_cols = set(sales_df.columns)
        missing_s = expected_cols["sales"] - s_cols
        if missing_s:
            errors.append(f"Sales dataset missing required columns: {missing_s}")
        else:
            if (sales_df["revenue"] < 0).any():
                errors.append("Sales dataset contains negative revenue values.")

            won_mask = sales_df["sales_stage"].astype(str).str.lower().str.contains("won")
            stats["won_customers"] = int(won_mask.sum())
            stats["total_revenue"] = float(sales_df.loc[won_mask, "revenue"].sum())
    else:
        warnings.append("Sales dataset is missing. Closed revenue and attribution cannot be computed.")
        unsupported_metrics.extend(["Total Attributed Revenue", "Average Deal Value", "Customers Acquired"])

    # 4. JOURNEY VALIDATION
    if journey_df is not None and not journey_df.empty:
        j_cols = set(journey_df.columns)
        missing_j = expected_cols["journey"] - j_cols
        if missing_j:
            warnings.append(f"Customer journey dataset missing: {missing_j}. Multi-touch attribution will use fallback.")
            unsupported_metrics.append("Multi-touch Attribution Models")
        else:
            stats["total_touchpoints"] = len(journey_df)
    else:
        info.append("Customer journey touchpoints are not provided. Single-touch attribution fallback will be used.")

    # 5. REFERENTIAL INTEGRITY
    if campaigns_df is not None and leads_df is not None and "campaign_id" in campaigns_df.columns and "campaign_id" in leads_df.columns:
        valid_camp_ids = set(campaigns_df["campaign_id"].dropna().unique())
        lead_camp_ids = set(leads_df["campaign_id"].dropna().unique())
        orphan_leads = lead_camp_ids - valid_camp_ids
        if orphan_leads:
            warnings.append(f"Found {len(orphan_leads)} campaign IDs in Leads that do not exist in Campaigns: {list(orphan_leads)[:3]}")

    if leads_df is not None and sales_df is not None and "customer_id" in leads_df.columns and "customer_id" in sales_df.columns:
        valid_lead_custs = set(leads_df["customer_id"].dropna().unique())
        sales_custs = set(sales_df["customer_id"].dropna().unique())
        orphan_sales = sales_custs - valid_lead_custs
        if orphan_sales:
            warnings.append(f"Found {len(orphan_sales)} customer IDs in Sales with no matching record in Leads.")

    is_valid = len(errors) == 0

    return {
        "is_valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "info": info,
        "unsupported_metrics": list(set(unsupported_metrics)),
        "stats": stats
    }
