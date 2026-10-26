"""
Automated unit tests for data validation, schema checks and referential integrity.
"""

import pytest
import pandas as pd
from modules.data_loader import validate_datasets


def test_validation_missing_columns():
    invalid_campaigns = pd.DataFrame([{"wrong_col": 1}])
    leads = pd.DataFrame([{"lead_id": "L1", "customer_id": "C1", "campaign_id": "CMP1"}])

    val = validate_datasets(campaigns_df=invalid_campaigns, leads_df=leads)
    assert not val["is_valid"]
    assert any("Campaigns dataset missing required columns" in err for err in val["errors"])


def test_validation_negative_values():
    campaigns = pd.DataFrame([{"campaign_id": "CMP1", "channel": "Google", "spend": -500.0}])
    leads = pd.DataFrame([{"lead_id": "L1", "customer_id": "C1", "campaign_id": "CMP1"}])

    val = validate_datasets(campaigns_df=campaigns, leads_df=leads)
    assert not val["is_valid"]
    assert any("negative spend" in err for err in val["errors"])


def test_referential_integrity_warning():
    campaigns = pd.DataFrame([{"campaign_id": "CMP1", "channel": "Google", "spend": 500.0}])
    leads = pd.DataFrame([{"lead_id": "L1", "customer_id": "C1", "campaign_id": "CMP999"}])  # Unknown campaign

    val = validate_datasets(campaigns_df=campaigns, leads_df=leads)
    assert val["is_valid"]  # orphan campaign in leads is treated as a warning
    assert any("do not exist in Campaigns" in w for w in val["warnings"])
