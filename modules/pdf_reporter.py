"""
RevenueLens AI - Management PDF Report Generator
Generates a polished, C-suite ready PDF executive brief using ReportLab.
Includes executive summary, KPI tables, funnel drop-off audit, attribution breakdown,
lead machine learning diagnostics, prioritized recommendations, and methodology disclaimers.
"""

import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)


def generate_executive_pdf_report(
    kpis: dict,
    funnel_data: dict,
    attribution_data: dict,
    campaign_data,
    ml_results: dict,
    leakage_issues: list,
    action_plan: list,
    executive_narrative: str
) -> io.BytesIO:
    """
    Generate an in-memory PDF buffer with a complete executive report.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    story = []
    styles = getSampleStyleSheet()

    # Brand Colors
    PRIMARY = colors.HexColor("#1E3A8A")    # Deep Navy
    SECONDARY = colors.HexColor("#2563EB")  # Royal Blue
    ACCENT = colors.HexColor("#0D9488")     # Teal
    DARK_GRAY = colors.HexColor("#1F2937")  # Slate 800
    LIGHT_BG = colors.HexColor("#F8FAFC")   # Slate 50
    BORDER_COLOR = colors.HexColor("#E2E8F0")

    # Typography Styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=PRIMARY,
        spaceAfter=4
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#64748B"),
        spaceAfter=12
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=PRIMARY,
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=DARK_GRAY,
        spaceAfter=6
    )

    callout_style = ParagraphStyle(
        "Callout",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1E293B")
    )

    table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=DARK_GRAY
    )

    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=table_cell,
        fontName="Helvetica-Bold"
    )

    # 1. HEADER & TITLE
    story.append(Paragraph("RevenueLens AI | Executive Briefing", title_style))
    story.append(Paragraph(
        f"Marketing-to-Revenue Attribution & Funnel Intelligence Diagnostic Report • Generated: {datetime.now().strftime('%B %d, %Y')}",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=1.5, color=SECONDARY, spaceBefore=0, spaceAfter=10))

    # 2. EXECUTIVE SUMMARY
    story.append(Paragraph("1. Executive Summary & Root Cause Diagnosis", section_heading))
    clean_narrative = executive_narrative.replace("#", "").replace("**", "")
    for para in clean_narrative.split("\n\n"):
        if para.strip():
            story.append(Paragraph(para.strip(), body_style))
    story.append(Spacer(1, 8))

    # 3. CORE FINANCIAL & MARKETING KPIS TABLE
    story.append(Paragraph("2. Financial & Growth KPIs Overview", section_heading))
    spend = kpis.get("spend", 0.0)
    rev = kpis.get("revenue", 0.0)
    roas = kpis.get("roas", 0.0)
    roi = kpis.get("roi", 0.0)
    leads = kpis.get("leads", 0)
    cust = kpis.get("customers", 0)
    cpl = kpis.get("cpl", 0.0)
    cac = kpis.get("cac", 0.0)
    conv = kpis.get("conversion_rate", 0.0)
    deal_val = kpis.get("avg_deal_value", 0.0)

    kpi_matrix = [
        [
            Paragraph("Total Marketing Spend", table_cell_bold), Paragraph(f"${spend:,.0f}", table_cell),
            Paragraph("Attributed Revenue", table_cell_bold), Paragraph(f"${rev:,.0f}", table_cell),
        ],
        [
            Paragraph("Return on Ad Spend (ROAS)", table_cell_bold), Paragraph(f"{roas:.2f}x", table_cell),
            Paragraph("Marketing ROI", table_cell_bold), Paragraph(f"{roi:+.1f}%", table_cell),
        ],
        [
            Paragraph("Total Leads Generated", table_cell_bold), Paragraph(f"{leads:,}", table_cell),
            Paragraph("Customers Acquired", table_cell_bold), Paragraph(f"{cust:,}", table_cell),
        ],
        [
            Paragraph("Cost Per Lead (CPL)", table_cell_bold), Paragraph(f"${cpl:.2f}", table_cell),
            Paragraph("Customer Acquisition Cost", table_cell_bold), Paragraph(f"${cac:,.2f}", table_cell),
        ],
        [
            Paragraph("Lead-to-Customer Conv.", table_cell_bold), Paragraph(f"{conv:.2f}%", table_cell),
            Paragraph("Average Deal Value (ACV)", table_cell_bold), Paragraph(f"${deal_val:,.0f}", table_cell),
        ]
    ]

    kpi_table = Table(kpi_matrix, colWidths=[130, 140, 130, 140])
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 10))

    # 4. FUNNEL BOTTLENECK ANALYSIS
    story.append(Paragraph("3. Customer Journey Funnel Drop-off Analysis", section_heading))
    funnel_df = funnel_data.get("funnel_df") if isinstance(funnel_data, dict) else None
    if funnel_df is not None and not funnel_df.empty:
        funnel_rows = [
            [
                Paragraph("Funnel Stage", table_cell_bold),
                Paragraph("Volume", table_cell_bold),
                Paragraph("Conversion %", table_cell_bold),
                Paragraph("Drop-off %", table_cell_bold),
                Paragraph("Lost Opportunity ($)", table_cell_bold)
            ]
        ]
        for _, r in funnel_df.iterrows():
            funnel_rows.append([
                Paragraph(str(r["stage_name"]), table_cell),
                Paragraph(f"{int(r['count']):,}", table_cell),
                Paragraph(f"{r['conversion_from_prev_pct']:.1f}%", table_cell),
                Paragraph(f"{r['drop_off_pct']:.1f}%", table_cell),
                Paragraph(f"${r['lost_revenue_opportunity']:,.0f}", table_cell)
            ])

        f_table = Table(funnel_rows, colWidths=[160, 80, 90, 80, 130])
        f_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(f_table)
    story.append(Spacer(1, 10))

    # 5. REVENUE ATTRIBUTION COMPARISON
    story.append(Paragraph("4. Multi-Touch Attribution by Channel", section_heading))
    ch_attr = attribution_data.get("channel_attribution") if isinstance(attribution_data, dict) else None
    if ch_attr is not None and not ch_attr.empty:
        attr_rows = [
            [
                Paragraph("Marketing Channel", table_cell_bold),
                Paragraph("Spend ($)", table_cell_bold),
                Paragraph("Attributed Rev ($)", table_cell_bold),
                Paragraph("Rev Share %", table_cell_bold),
                Paragraph("ROAS", table_cell_bold),
                Paragraph("CAC ($)", table_cell_bold)
            ]
        ]
        for _, r in ch_attr.iterrows():
            attr_rows.append([
                Paragraph(str(r["channel"]), table_cell),
                Paragraph(f"${r.get('spend', 0):,.0f}", table_cell),
                Paragraph(f"${r.get('attributed_revenue', 0):,.0f}", table_cell),
                Paragraph(f"{r.get('revenue_share_pct', 0):.1f}%", table_cell),
                Paragraph(f"{r.get('roas', 0):.2f}x", table_cell),
                Paragraph(f"${r.get('cac', 0):,.0f}", table_cell)
            ])

        a_table = Table(attr_rows, colWidths=[140, 80, 100, 70, 70, 80])
        a_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(a_table)
    story.append(Spacer(1, 10))

    # 6. TOP DETECTED LEAKAGES
    story.append(Paragraph("5. AI-Detected Revenue Leakage Incidents", section_heading))
    if leakage_issues:
        for idx, issue in enumerate(leakage_issues[:4], 1):
            p_text = f"<b>{idx}. [{issue.get('priority', 'Medium')} Priority] {issue.get('problem')}</b>"
            story.append(Paragraph(p_text, table_cell_bold))
            story.append(Paragraph(f"• <b>Evidence:</b> {issue.get('evidence')}", body_style))
            story.append(Paragraph(f"• <b>Action:</b> {issue.get('recommendation')}", body_style))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("No critical revenue leakages detected above warning thresholds.", body_style))
    story.append(Spacer(1, 8))

    # 7. PRIORITIZED ACTION ROADMAP
    story.append(Paragraph("6. Prioritized Marketing Optimization Action Plan", section_heading))
    if action_plan:
        act_rows = [
            [
                Paragraph("Horizon", table_cell_bold),
                Paragraph("Priority", table_cell_bold),
                Paragraph("Strategic Directive & Recommended Action", table_cell_bold),
                Paragraph("KPI to Monitor", table_cell_bold)
            ]
        ]
        for act in action_plan[:5]:
            act_rows.append([
                Paragraph(act.get("timeframe", ""), table_cell),
                Paragraph(act.get("priority", ""), table_cell_bold),
                Paragraph(f"{act.get('action', '')}<br/><font color='#64748B'>{act.get('expected_impact', '')}</font>", table_cell),
                Paragraph(act.get("kpi_to_monitor", ""), table_cell)
            ])

        act_table = Table(act_rows, colWidths=[100, 60, 260, 120])
        act_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
            ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(act_table)
    story.append(Spacer(1, 12))

    # 8. METHODOLOGY & LIMITATIONS DISCLAIMER
    story.append(Paragraph("7. Data Governance, Methodology & Analytical Disclaimers", section_heading))
    disclaimer_text = (
        "<b>Attribution Modeling:</b> Multi-touch attribution distributes recognized deal revenue across recorded touchpoints. "
        "Attribution results estimate relative channel contribution and should not be confused with causal incrementality testing.<br/>"
        "<b>Lead Scoring & ML Models:</b> Predictive lead probabilities are generated via supervised classification (Random Forest/Logistic Regression). "
        "Correlations identify statistical likelihood and do not guarantee future conversion.<br/>"
        "<b>Synthetic Data Disclaimer:</b> Where synthetic datasets are utilized, figures illustrate systemic modeling mechanics "
        "and do not represent confidential proprietary financial records."
    )
    story.append(Paragraph(disclaimer_text, callout_style))

    # Build PDF
    doc.build(story)
    buffer.seek(0)
    return buffer
