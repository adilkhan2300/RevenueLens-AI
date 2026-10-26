"""
RevenueLens AI - Lead Conversion Machine Learning Engine
Builds classification models (Logistic Regression and Random Forest) to predict
lead conversion probability, computes evaluation metrics (Precision, Recall, F1, ROC-AUC),
extracts feature importances, and segments leads into actionable risk tiers.
Prevents data leakage by strictly omitting post-conversion sales attributes.
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, roc_curve
)


def prepare_lead_dataset(leads_df: pd.DataFrame, sales_df: pd.DataFrame = None) -> tuple:
    """
    Prepare feature matrix X and target y, strictly preventing data leakage.
    Target: 1 if converted to won deal, 0 otherwise.
    """
    if leads_df is None or leads_df.empty:
        return None, None, "Leads dataset is empty."

    df = leads_df.copy()

    # Determine ground truth target
    if "is_converted" in df.columns:
        y = df["is_converted"].astype(int)
    elif sales_df is not None and not sales_df.empty:
        won_custs = set(sales_df[sales_df["sales_stage"].astype(str).str.lower().str.contains("won")]["customer_id"])
        y = df["customer_id"].isin(won_custs).astype(int)
    else:
        return None, None, "No conversion target column (is_converted or matching won sales) found."

    # Prevent Data Leakage: strictly omit sales pipeline results, deal revenue, close date, opportunity IDs
    leakage_cols = [
        "is_converted", "customer_id", "lead_id", "lead_date",
        "sales_stage", "conversion_status", "close_date", "revenue", "opportunity_id"
    ]
    candidate_features = [col for col in df.columns if col not in leakage_cols]

    # Desired feature columns
    numerical_cols = [c for c in ["lead_score", "follow_up_time_hours", "num_interactions"] if c in candidate_features]
    categorical_cols = [c for c in ["lead_source", "campaign_id", "industry", "company_size", "engagement_level", "qualification_status"] if c in candidate_features]

    all_features = numerical_cols + categorical_cols
    if not all_features:
        return None, None, "No suitable predictive features available in the dataset."

    X = df[all_features].copy()
    return X, y, (numerical_cols, categorical_cols)


def train_lead_conversion_models(
    leads_df: pd.DataFrame,
    sales_df: pd.DataFrame = None,
    test_size: float = 0.25,
    random_state: int = 42
) -> dict:
    """
    Train and evaluate Logistic Regression and Random Forest models.
    Returns metrics, pipelines, feature importances, and scored predictions.
    """
    X, y, feature_meta = prepare_lead_dataset(leads_df, sales_df)
    if X is None:
        return {"error": feature_meta}

    numerical_cols, categorical_cols = feature_meta

    if len(X) < 50:
        return {"error": "Dataset has fewer than 50 leads. Insufficient data for reliable statistical machine learning."}

    # Verify both classes exist in y
    if y.nunique() < 2:
        return {"error": "Target contains only one class. Cannot train a binary classifier."}

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    # Preprocessing pipelines
    num_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    cat_transformer = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_transformer, numerical_cols),
            ("cat", cat_transformer, categorical_cols)
        ]
    )

    # 1. Logistic Regression
    lr_pipe = Pipeline([
        ("preprocessor", preprocessor),
        ("clf", LogisticRegression(max_iter=1000, random_state=random_state, class_weight="balanced"))
    ])
    lr_pipe.fit(X_train, y_train)

    # 2. Random Forest
    rf_pipe = Pipeline([
        ("preprocessor", preprocessor),
        ("clf", RandomForestClassifier(n_estimators=120, max_depth=8, random_state=random_state, class_weight="balanced"))
    ])
    rf_pipe.fit(X_train, y_train)

    # Predictions & probabilities on test set
    models_evaluated = {}
    for name, pipe in [("Logistic Regression", lr_pipe), ("Random Forest", rf_pipe)]:
        y_pred = pipe.predict(X_test)
        y_prob = pipe.predict_proba(X_test)[:, 1]

        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        auc = roc_auc_score(y_test, y_prob) if y.nunique() > 1 else 0.5
        cm = confusion_matrix(y_test, y_pred).tolist()
        fpr, tpr, _ = roc_curve(y_test, y_prob)

        models_evaluated[name] = {
            "pipeline": pipe,
            "accuracy": round(acc, 3),
            "precision": round(prec, 3),
            "recall": round(rec, 3),
            "f1": round(f1, 3),
            "roc_auc": round(auc, 3),
            "confusion_matrix": cm,
            "fpr": fpr.tolist(),
            "tpr": tpr.tolist()
        }

    # Extract Feature Importances from Random Forest
    rf_model = rf_pipe.named_steps["clf"]
    cat_feature_names = []
    if categorical_cols:
        cat_encoder = rf_pipe.named_steps["preprocessor"].named_transformers_["cat"].named_steps["onehot"]
        cat_feature_names = list(cat_encoder.get_feature_names_out(categorical_cols))

    all_feat_names = numerical_cols + cat_feature_names
    importances = rf_model.feature_importances_

    feat_imp_df = pd.DataFrame({
        "feature": all_feat_names,
        "importance": importances
    }).sort_values(by="importance", ascending=False).head(15).reset_index(drop=True)

    # Score the entire dataset using the higher performing model (default Random Forest)
    primary_pipe = rf_pipe if models_evaluated["Random Forest"]["roc_auc"] >= models_evaluated["Logistic Regression"]["roc_auc"] else lr_pipe
    all_probs = primary_pipe.predict_proba(X)[:, 1]

    scored_leads = leads_df.copy()
    scored_leads["predicted_conversion_prob"] = np.round(all_probs, 3)

    def assign_tier(p):
        if p >= 0.65:
            return "High (>65%)"
        elif p >= 0.35:
            return "Medium (35-65%)"
        else:
            return "Low (<35%)"

    scored_leads["conversion_tier"] = scored_leads["predicted_conversion_prob"].apply(assign_tier)

    tier_summary = scored_leads["conversion_tier"].value_counts().to_dict()

    return {
        "error": None,
        "models": models_evaluated,
        "best_model_name": "Random Forest" if models_evaluated["Random Forest"]["roc_auc"] >= models_evaluated["Logistic Regression"]["roc_auc"] else "Logistic Regression",
        "feature_importance": feat_imp_df,
        "scored_leads": scored_leads,
        "tier_summary": tier_summary,
        "numerical_cols": numerical_cols,
        "categorical_cols": categorical_cols,
        "test_sample_size": len(X_test),
        "train_sample_size": len(X_train)
    }


def predict_single_lead(
    model_pipeline,
    lead_input: dict
) -> tuple:
    """
    Score an individual lead given interactive user inputs.
    Returns predicted probability (float) and recommended strategic action (str).
    """
    input_df = pd.DataFrame([lead_input])
    prob = float(model_pipeline.predict_proba(input_df)[0, 1])

    if prob >= 0.70:
        action = "High Conversion Potential (VIP): Route directly to senior sales rep within 1 hour. Schedule direct discovery call."
        tier = "High"
    elif prob >= 0.40:
        action = "Moderate Conversion Potential: Enroll in targeted multi-touch email nurture sequence. Follow up within 12 hours."
        tier = "Medium"
    else:
        action = "Low Conversion Potential: Keep in automated low-touch marketing nurture. Re-qualify before expending direct sales time."
        tier = "Low"

    return prob, tier, action
