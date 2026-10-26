"""
Automated unit tests for 5 attribution models and normalization constraints.
"""

import pytest
import pandas as pd
from modules.attribution_engine import calculate_attribution


@pytest.fixture
def sample_attribution_data():
    journey = pd.DataFrame([
        {"customer_id": "C1", "campaign_id": "CMP1", "channel": "Google Ads", "touchpoint_timestamp": "2025-01-01 10:00:00"},
        {"customer_id": "C1", "campaign_id": "CMP2", "channel": "Email", "touchpoint_timestamp": "2025-01-05 10:00:00"},
        {"customer_id": "C1", "campaign_id": "CMP3", "channel": "LinkedIn", "touchpoint_timestamp": "2025-01-10 10:00:00"},
        {"customer_id": "C2", "campaign_id": "CMP1", "channel": "Google Ads", "touchpoint_timestamp": "2025-01-03 10:00:00"},
        {"customer_id": "C2", "campaign_id": "CMP3", "channel": "LinkedIn", "touchpoint_timestamp": "2025-01-07 10:00:00"},
    ])
    sales = pd.DataFrame([
        {"customer_id": "C1", "sales_stage": "Closed-Won", "revenue": 10000.0, "close_date": "2025-01-15"},
        {"customer_id": "C2", "sales_stage": "Closed-Won", "revenue": 5000.0, "close_date": "2025-01-12"},
    ])
    campaigns = pd.DataFrame([
        {"campaign_id": "CMP1", "campaign_name": "Camp 1", "channel": "Google Ads", "spend": 2000.0},
        {"campaign_id": "CMP2", "campaign_name": "Camp 2", "channel": "Email", "spend": 500.0},
        {"campaign_id": "CMP3", "campaign_name": "Camp 3", "channel": "LinkedIn", "spend": 3000.0},
    ])
    return journey, sales, campaigns


def test_attribution_normalization_all_models(sample_attribution_data):
    journey, sales, campaigns = sample_attribution_data
    total_sales_rev = sales["revenue"].sum()

    for model_name in ["First-Touch", "Last-Touch", "Linear", "Position-Based (U-Shaped)", "Time-Decay (7-Day Half-Life)"]:
        result = calculate_attribution(journey, sales, campaigns, model=model_name)
        ch_attr = result["channel_attribution"]

        attributed_sum = ch_attr["attributed_revenue"].sum()
        assert attributed_sum == pytest.approx(total_sales_rev, abs=0.01), f"Model {model_name} attribution does not sum to total revenue."


def test_first_touch_attribution_logic(sample_attribution_data):
    journey, sales, campaigns = sample_attribution_data
    result = calculate_attribution(journey, sales, campaigns, model="First-Touch")
    ch_attr = result["channel_attribution"].set_index("channel")["attributed_revenue"]

    # Both C1 and C2 had Google Ads as their first touchpoint
    assert ch_attr.get("Google Ads", 0) == pytest.approx(15000.0)
    assert ch_attr.get("Email", 0) == pytest.approx(0.0)
    assert ch_attr.get("LinkedIn", 0) == pytest.approx(0.0)


def test_last_touch_attribution_logic(sample_attribution_data):
    journey, sales, campaigns = sample_attribution_data
    result = calculate_attribution(journey, sales, campaigns, model="Last-Touch")
    ch_attr = result["channel_attribution"].set_index("channel")["attributed_revenue"]

    # Both C1 and C2 had LinkedIn as their last touchpoint
    assert ch_attr.get("LinkedIn", 0) == pytest.approx(15000.0)
    assert ch_attr.get("Google Ads", 0) == pytest.approx(0.0)
