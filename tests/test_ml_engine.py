"""
Automated unit tests for lead conversion machine learning engine and data leakage prevention.
"""

import pytest
import pandas as pd
import numpy as np
from modules.lead_ml_engine import prepare_lead_dataset, train_lead_conversion_models, predict_single_lead


def test_lead_dataset_leakage_prevention():
    leads = pd.DataFrame([
        {
            "lead_id": f"L{i}",
            "customer_id": f"C{i}",
            "campaign_id": "CMP1",
            "lead_source": "Google Ads",
            "lead_score": 60 + i % 30,
            "qualification_status": "SQL",
            "industry": "Tech",
            "company_size": "51-200",
            "follow_up_time_hours": 3.5,
            "engagement_level": "High",
            "num_interactions": 4,
            "is_converted": i % 2,
            "revenue": 10000.0,      # Leaked column
            "sales_stage": "Won"     # Leaked column
        }
        for i in range(80)
    ])

    X, y, (num_cols, cat_cols) = prepare_lead_dataset(leads)

    assert "revenue" not in X.columns
    assert "sales_stage" not in X.columns
    assert "is_converted" not in X.columns
    assert "customer_id" not in X.columns
    assert len(X) == 80
    assert len(y) == 80


def test_train_lead_conversion_models_execution():
    np.random.seed(42)
    leads = pd.DataFrame([
        {
            "lead_id": f"L{i}",
            "customer_id": f"C{i}",
            "campaign_id": "CMP1" if i % 2 == 0 else "CMP2",
            "lead_source": "Google Ads" if i % 2 == 0 else "Meta Ads",
            "lead_score": int(np.random.randint(20, 95)),
            "qualification_status": "SQL" if i % 3 == 0 else "MQL",
            "industry": "Technology & SaaS",
            "company_size": "51-200",
            "follow_up_time_hours": float(np.random.uniform(1.0, 48.0)),
            "engagement_level": "Medium",
            "num_interactions": int(np.random.randint(1, 8)),
            "is_converted": 1 if i % 4 == 0 else 0
        }
        for i in range(120)
    ])

    results = train_lead_conversion_models(leads)
    assert results["error"] is None
    assert "Random Forest" in results["models"]
    assert "Logistic Regression" in results["models"]
    assert results["models"]["Random Forest"]["roc_auc"] >= 0.5
    assert not results["feature_importance"].empty
    assert "predicted_conversion_prob" in results["scored_leads"].columns
