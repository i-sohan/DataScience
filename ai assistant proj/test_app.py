import os
import sys
import json
import pandas as pd
from pathlib import Path

print("==================================================")
print(" VERIFYING GENAI BUSINESS ANALYTICS ASSISTANT")
print("==================================================")

try:
    # 1. Config & Database Init
    from config import BASE_DIR, DATASET_FOLDER, UPLOAD_FOLDER, DB_PATH
    from database.db import init_db, register_dataset, get_dataset, list_all_datasets, add_chat_message, get_chat_history
    
    init_db()
    print("[1/6] Database initialized successfully at:", DB_PATH)

    # 2. Test Cleaning Engine
    from services.cleaner import clean_dataset
    sales_sample = DATASET_FOLDER / 'sample_sales.csv'
    cleaned_sales = UPLOAD_FOLDER / 'test_cleaned_sales.csv'
    table_name = "test_sales_table"
    
    df_cleaned, audit = clean_dataset(sales_sample, cleaned_sales, table_name)
    print(f"[2/6] Auto-Cleaner verified: Cleaned {len(df_cleaned)} rows. Duplicates removed: {audit['duplicates_removed']}.")
    print("      Converted columns:", audit['columns_converted'])

    # 3. Test Profiling & Analyzer Engine
    from services.analyzer import profile_dataset, execute_sql_query
    summary = profile_dataset(df_cleaned)
    summary['audit'] = audit
    print(f"[3/6] Profiler verified: Found {summary['total_cols']} columns, {len(summary['kpis'])} KPI metrics.")

    register_dataset("test_ds_sales", "sample_sales.csv", sales_sample, cleaned_sales, len(df_cleaned), len(df_cleaned.columns), summary, table_name)
    ds = get_dataset("test_ds_sales")
    assert ds is not None, "Dataset registration failed"

    # 4. Test LLM & Query Engine
    from services.llm import process_natural_language_question
    q1 = "Which products made the highest profit in Karnataka?"
    res_q1 = process_natural_language_question("test_ds_sales", table_name, df_cleaned, q1)
    print(f"[4/6] AI Analytics Engine verified for question: '{q1}'")
    print(f"      SQL Generated: {res_q1['sql']}")
    print(f"      Rows Returned: {res_q1['query_result'].get('row_count', 0)}")
    print(f"      Narrative Insight Sample: {res_q1['business_insight'][:120].encode('ascii', 'ignore').decode('ascii')}...")

    # 5. Test Chart Generator & Forecasting Engine
    from services.charts import build_chart_json, create_dashboard_charts
    from services.forecaster import forecast_metric
    
    charts = create_dashboard_charts(df_cleaned)
    print(f"[5/6] Plotly Chart Engine verified: Generated {len(charts)} interactive chart specs.")
    
    fc = forecast_metric(df_cleaned, date_col='Date', metric_col='Profit', forecast_periods=6)
    assert 'chart_spec' in fc, "Forecast model failed"
    print(f"      Forecaster model verified: 6-period profit trend projected. Total predicted: {fc['total_predicted']}")

    # 6. Test PDF Report Generator
    from services.report_generator import generate_pdf_report
    pdf_path = generate_pdf_report(ds, summary, get_chat_history("test_ds_sales"))
    assert pdf_path.exists(), "PDF report generation failed"
    print(f"[6/6] PDF Report Builder verified: Generated executive report at {pdf_path.name}")

    print("\n==================================================")
    print(" ALL SYSTEM COMPONENTS VERIFIED 100% SUCCESSFULLY!")
    print("==================================================")

except Exception as e:
    print(f"VERIFICATION FAILED WITH ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
