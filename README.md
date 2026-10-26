# RevenueLens AI – Marketing-to-Revenue Attribution & Funnel Intelligence

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.49+-FF4B4B.svg)](https://streamlit.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An intelligent, AI-powered web analytics platform built for CMOs, CROs, Revenue Operations, and MBA Marketing & Data Science academic analysis.

**RevenueLens AI** diagnoses the classic commercial dilemma: **"Why are we generating thousands of marketing leads, but experiencing sluggish revenue growth?"** It traces the full buyer journey from top-of-funnel impression to closed-won cash flow, uncovering hidden drop-offs, identifying capital misallocations ("Vanity Traps"), and attributing revenue across 5 multi-touch models.

---

## 🌟 Key Features & Core Modules

### 1. 📊 Executive Overview
- Real-time KPI scorecard: Total Spend, Attributed Revenue, ROAS, Marketing ROI, Average Deal Value (ACV), CPL, CAC, and Lead-to-Customer Conversion Rate.
- Period-over-period comparisons with automated percentage deltas and trend indicators.
- Spend vs. Revenue by channel visualizer.
- High-priority automated bottleneck alerts.

### 2. 🌪️ 9-Stage Customer Journey & Funnel Intelligence
- Complete 9-stage funnel visualization:
  1. *Impressions* $\rightarrow$ 2. *Clicks* $\rightarrow$ 3. *Visits* $\rightarrow$ 4. *Leads* $\rightarrow$ 5. *MQL* $\rightarrow$ 6. *SQL* $\rightarrow$ 7. *Opportunities* $\rightarrow$ 8. *Closed-Won Customers* $\rightarrow$ 9. *Revenue*.
- Stage-to-stage transition rates, drop-off percentages, lost prospect counts, and **estimated lost dollar value opportunity**.
- Interactive stage drill-down by marketing channel and customer industry segment.

### 3. ⚖️ Multi-Touch Marketing Attribution Engine
- Evaluates 5 transparent mathematical attribution models:
  - **First-Touch Attribution:** 100% credit to initial discovery.
  - **Last-Touch Attribution:** 100% credit to final conversion.
  - **Linear Attribution:** Equal credit ($1/N$) across all journey interactions.
  - **Position-Based (U-Shaped) Attribution:** 40% First, 40% Last, 20% Middle.
  - **Time-Decay Attribution:** Exponential half-life decay ($\lambda = 7$ days).
- Mathematical normalization ensures total attributed revenue across channels strictly equals recognized deal revenue.
- Side-by-side grouped model comparison chart and fallback support for single-touch datasets.

### 4. 📈 Campaign Performance & Strategic Quadrants
- Channel-level unit economics: CPL vs. CAC, CTR, conversion rates, and ROI.
- Strategic classification of campaigns into MBA quadrants:
  - 🚨 **Vanity Trap:** High volume leads, low qualification, near-zero revenue.
  - 💎 **Hidden Gem:** Modest lead volume, high lead score, superior ROAS.
  - 💸 **Money Pit:** Heavy expenditure, negative net ROI.
  - 🚀 **Scale Candidate:** High volume, high conversion, positive unit economics.

### 5. 🤖 Lead Intelligence & Machine Learning Engine
- Supervised classification using **Logistic Regression** and **Random Forest**.
- Rigorous data leakage prevention: restricts features to attributes known at time of lead capture.
- Diagnostic benchmarks: Accuracy, Precision, Recall, F1-Score, and ROC-AUC curves.
- Feature importance ranking (e.g., impact of speed-to-lead follow-up time).
- Risk segmentation into High (>65%), Medium (35-65%), and Low (<35%) probability tiers.
- **Interactive Lead Scorer widget** for real-time conversion probability forecasting.

### 6. 💡 AI-Powered Revenue Leakage Detection
- 10+ transparent, metric-based heuristics detecting:
  - Lead Bloat / Vanity Traps
  - Capital Bleed & Inefficient Channels
  - MQL-to-SQL Sales Choke Points
  - Speed-to-Lead Follow-up Latency (>24h decay)
  - Revenue Concentration Risk
  - Channel Volume vs. Value Divergence
- Dual-mode executive synthesis: Deterministic rule-based briefing (100% offline) + optional OpenAI LLM narrative integration.
- C-Suite publication-ready **Executive PDF Report generator** powered by ReportLab.

### 7. 🎛️ What-If Scenario Simulator
- Interactive executive levers: budget scaling, budget reallocation boost, CPL adjustments, qualification enhancements, and ACV expansion.
- Mathematically consistent projections without double-counting stage gains.
- Comparative baseline vs. scenario ledger and delta bar charts.

### 8. 💾 Data Management, Upload & Validation
- CSV and Excel upload support for Campaigns, Leads, Journey, and Sales datasets.
- Schema verification, column mapping, negative value checks, and referential integrity audits.
- SQLite database persistence with instant synthetic benchmark reset.
- Downloadable pre-formatted data templates.

### 9. 📖 Methodology & Definitions
- Comprehensive documentation of all mathematical formulas, attribution algorithms, ML architectures, and academic disclaimers.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend & UI** | Streamlit, Custom SaaS CSS, Responsive Grid |
| **Data Processing** | Python 3.10+, Pandas, NumPy |
| **Interactive Visualizations** | Plotly (Go, Express) |
| **Machine Learning** | Scikit-learn (Logistic Regression, Random Forest, ColumnTransformer) |
| **Database** | SQLite3 |
| **Reporting** | ReportLab (Management PDF generation) |
| **Testing** | Pytest |
| **AI Synthesis** | OpenAI API (Optional) & Deterministic Rule Engine (Default) |

---

## 📁 Repository Structure

```
revenue_lens_ai/
├── app.py                      # Streamlit application entry point & page router
├── .streamlit/
│   └── config.toml             # Custom SaaS theme and server settings
├── modules/
│   ├── data_loader.py          # Synthetic generator, validation & SQLite manager
│   ├── kpi_engine.py           # Core KPI formulas and period comparisons
│   ├── funnel_engine.py        # 9-stage funnel analytics & drop-off audit
│   ├── attribution_engine.py   # 5 attribution models & normalization engine
│   ├── campaign_analytics.py   # Strategic quadrants, CPL vs CAC, trends
│   ├── lead_ml_engine.py       # Scikit-learn classification & lead scoring
│   ├── leakage_detector.py     # Heuristic revenue leakage detector
│   ├── scenario_simulator.py   # What-if forecasting engine
│   ├── ai_insights.py          # Strategic roadmap & hybrid LLM synthesis
│   └── pdf_reporter.py         # Management-ready PDF report generator
├── data/
│   ├── sample/                 # Realistic synthetic benchmark CSVs
│   ├── templates/              # Clean CSV & Excel data templates
│   └── database.db             # Local SQLite database
├── tests/
│   ├── test_kpi_engine.py      # Automated unit tests for KPI formulas
│   ├── test_attribution.py     # Automated tests for attribution models
│   ├── test_validation.py      # Automated tests for schema & data integrity
│   └── test_ml_engine.py       # Automated tests for ML pipeline & leakage checks
├── conftest.py                 # Pytest configuration
├── pytest.ini                  # Pytest runner settings
├── requirements.txt            # Project dependencies
├── .env.example                # Environment variables template
└── README.md                   # Complete documentation
```

---

## 🚀 Quickstart & Installation

### 1. Clone or Open Workspace
```bash
cd "c:/Users/adil2/OneDrive/Desktop/Assignments/Shayam Sir IA/PB3"
```

### 2. Set Up Virtual Environment (Optional but Recommended)
```bash
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. (Optional) Configure OpenAI API Key
If you wish to use an LLM for conversational executive narratives, copy `.env.example` to `.env` and add your key:
```bash
cp .env.example .env
```
*(Note: If no API key is provided, the application automatically uses its built-in rule-based intelligence engine).*

### 5. Run the Automated Tests
```bash
python -m pytest -v
```
All 10 tests across KPIs, attribution models, ML leakage checks, and data validation will execute and pass.

### 6. Launch the Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 📐 Formulas & Core Calculations

- **CTR:**
  $$\text{CTR} = \frac{\text{Clicks}}{\text{Impressions}} \times 100$$
- **CPL:**
  $$\text{CPL} = \frac{\text{Marketing Spend}}{\text{Total Leads Generated}}$$
- **CAC:**
  $$\text{CAC} = \frac{\text{Marketing Spend}}{\text{Customers Acquired}}$$
- **Lead Conversion Rate:**
  $$\text{Conversion Rate} = \frac{\text{Customers Acquired}}{\text{Total Leads}} \times 100$$
- **ROAS:**
  $$\text{ROAS} = \frac{\text{Attributed Revenue}}{\text{Marketing Spend}}$$
- **Marketing ROI:**
  $$\text{Marketing ROI} = \frac{\text{Attributed Revenue} - \text{Marketing Spend}}{\text{Marketing Spend}} \times 100$$
- **Time-Decay Attribution:**
  $$w_i = 2^{-\frac{\Delta t_i}{\lambda}} \quad (\lambda = 7 \text{ days})$$

---

## ⚖️ Analytical Disclaimers
1. **Attribution Modeling:** Multi-touch models distribute recognized sales deal revenue across documented touchpoints. Attribution indicates relative channel contribution and should be coupled with incrementality testing for causal validation.
2. **Predictive Lead Scoring:** Lead scores and probabilities reflect supervised statistical associations from historical patterns. They do not constitute guaranteed future revenue outcomes.
3. **Synthetic Benchmark Data:** Pre-packaged sample data is synthetically engineered with a fixed seed (`seed=42`) to illustrate realistic enterprise marketing dynamics.
