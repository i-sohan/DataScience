import os
import json
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from config import REPORT_FOLDER

def generate_pdf_report(dataset_info: dict, summary_dict: dict, chat_history: list = None) -> Path:
    report_filename = f"Report_{dataset_info['filename']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    pdf_path = REPORT_FOLDER / report_filename
    
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=letter,
        rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40
    )
    
    styles = getSampleStyleSheet()
    
    # Custom Palette
    PRIMARY = colors.HexColor("#1e1b4b")
    SECONDARY = colors.HexColor("#4f46e5")
    ACCENT = colors.HexColor("#0284c7")
    TEXT_DARK = colors.HexColor("#1e293b")
    BG_LIGHT = colors.HexColor("#f8fafc")
    BORDER_COLOR = colors.HexColor("#e2e8f0")
    
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=24,
        leading=28,
        textColor=PRIMARY,
        fontName='Helvetica-Bold',
        spaceAfter=6
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=15
    )
    
    h2_style = ParagraphStyle(
        'Heading2Custom',
        parent=styles['Heading2'],
        fontSize=15,
        leading=18,
        textColor=SECONDARY,
        fontName='Helvetica-Bold',
        spaceBefore=14,
        spaceAfter=8
    )
    
    body_style = ParagraphStyle(
        'BodyCustom',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=TEXT_DARK,
        spaceAfter=6
    )

    kpi_title_style = ParagraphStyle('KPITitle', parent=body_style, fontSize=9, textColor=colors.HexColor("#64748b"))
    kpi_val_style = ParagraphStyle('KPIVal', parent=body_style, fontSize=14, leading=16, fontName='Helvetica-Bold', textColor=PRIMARY)

    elements = []
    
    # 1. Header Title Banner
    elements.append(Paragraph("Executive Business Analytics Report", title_style))
    elements.append(Paragraph(f"Dataset: <b>{dataset_info['filename']}</b> | Generated on: {datetime.now().strftime('%B %d, %Y - %H:%M')}", subtitle_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=SECONDARY, spaceBefore=0, spaceAfter=15))
    
    # 2. Executive Summary Metrics Grid
    elements.append(Paragraph("1. Executive Summary & KPIs", h2_style))
    
    kpis = summary_dict.get('kpis', {})
    kpi_cells = [
        [Paragraph("Total Rows", kpi_title_style), Paragraph(f"{summary_dict.get('total_rows', 0):,}", kpi_val_style)],
        [Paragraph("Total Columns", kpi_title_style), Paragraph(f"{summary_dict.get('total_cols', 0)}", kpi_val_style)]
    ]
    
    for metric_name, val_dict in kpis.items():
        kpi_cells.append([
            Paragraph(f"Total {metric_name}", kpi_title_style),
            Paragraph(f"₹{val_dict['total']:,.2f}" if val_dict['total'] > 1000 else f"{val_dict['total']:,.2f}", kpi_val_style)
        ])
        
    kpi_table_data = []
    # Organize into 2 columns of KPI cards
    for i in range(0, len(kpi_cells), 2):
        row = kpi_cells[i]
        if i + 1 < len(kpi_cells):
            row = row + kpi_cells[i+1]
        else:
            row = row + [Paragraph("", body_style), Paragraph("", body_style)]
        kpi_table_data.append(row)
        
    if kpi_table_data:
        t_kpi = Table(kpi_table_data, colWidths=[2.2*inch, 1.4*inch, 2.2*inch, 1.4*inch])
        t_kpi.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), BG_LIGHT),
            ('BOX', (0,0), (-1,-1), 1, BORDER_COLOR),
            ('INNERGRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
            ('PADDING', (0,0), (-1,-1), 8),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
        ]))
        elements.append(t_kpi)
        elements.append(Spacer(1, 15))
        
    # 3. Key Column Profiles & Distributions
    elements.append(Paragraph("2. Data Profiling Breakdown", h2_style))
    
    col_table_data = [["Column Name", "Data Type", "Null Count", "Unique Values", "Sample / Mean"]]
    for col_info in summary_dict.get('columns', [])[:8]:
        sample_str = str(col_info.get('mean', col_info.get('sample_values', [''])[0]))
        col_table_data.append([
            col_info['column'],
            col_info['dtype'],
            str(col_info['null_count']),
            str(col_info['unique_count']),
            sample_str[:25]
        ])
        
    t_cols = Table(col_table_data, colWidths=[1.8*inch, 1.2*inch, 1.0*inch, 1.2*inch, 2.0*inch])
    t_cols.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), SECONDARY),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,0), 9),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('BACKGROUND', (0,1), (-1,-1), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, BG_LIGHT]),
        ('FONTSIZE', (0,1), (-1,-1), 8.5),
    ]))
    elements.append(t_cols)
    elements.append(Spacer(1, 15))

    # 4. AI Analyst Answers & Query Insights
    if chat_history:
        elements.append(Paragraph("3. AI Analyst Business Queries & Insights", h2_style))
        for item in chat_history[:3]:
            elements.append(Paragraph(f"<b>Q: {item['user_query']}</b>", ParagraphStyle('QStyle', parent=body_style, fontName='Helvetica-Bold', textColor=ACCENT)))
            if item.get('generated_code'):
                elements.append(Paragraph(f"<i>SQL Executed:</i> <code>{item['generated_code']}</code>", ParagraphStyle('SQLStyle', parent=body_style, fontSize=8, textColor=colors.HexColor("#475569"))))
            ans_clean = item['answer_text'].replace('\n', '<br/>').replace('**', '<b>').replace('### ', '<b>').replace('#### ', '<b>')
            elements.append(Paragraph(ans_clean, body_style))
            elements.append(Spacer(1, 10))

    # Build PDF
    doc.build(elements)
    return pdf_path
