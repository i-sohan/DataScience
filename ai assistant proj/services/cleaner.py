import pandas as pd
import numpy as np
import re
import sqlite3
from pathlib import Path
from config import DB_PATH

def parse_currency(val):
    if pd.isna(val):
        return val
    if isinstance(val, (int, float)):
        return val
    val_str = str(val).strip()
    # Match currency formats like ₹50,000, $1,200.50, 50000 INR
    cleaned = re.sub(r'[₹$€£,]', '', val_str).strip()
    try:
        return float(cleaned)
    except ValueError:
        return val

def clean_dataset(input_file_path: Path, output_file_path: Path, table_name: str):
    # 1. Read file
    ext = input_file_path.suffix.lower()
    if ext in ['.xlsx', '.xls']:
        df_raw = pd.read_excel(input_file_path)
    else:
        df_raw = pd.read_csv(input_file_path)
    
    initial_shape = df_raw.shape
    df = df_raw.copy()
    
    # Audit tracking
    audit = {
        'initial_rows': initial_shape[0],
        'initial_cols': initial_shape[1],
        'duplicates_removed': 0,
        'nulls_handled': {},
        'columns_converted': [],
        'renamed_columns': {}
    }
    
    # 2. Clean column headers
    new_cols = []
    for c in df.columns:
        clean_c = str(c).strip()
        clean_c_var = re.sub(r'[^\w\s]', '', clean_c).strip().replace(' ', '_')
        if clean_c != c:
            audit['renamed_columns'][c] = clean_c_var
        new_cols.append(clean_c_var)
    df.columns = new_cols
    
    # 3. Deduplicate
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        df = df.drop_duplicates().reset_index(drop=True)
    audit['duplicates_removed'] = int(dup_count)
    
    # 4. Clean column values and infer types
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        if null_count > 0:
            audit['nulls_handled'][col] = null_count
        
        # Check string columns for currency/numeric or date formats
        if df[col].dtype == 'object':
            # Strip whitespace
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
            
            # Check if looks like currency
            sample_non_nulls = df[col].dropna().head(10).astype(str).tolist()
            if sample_non_nulls and any(re.search(r'[₹$€£]', s) for s in sample_non_nulls):
                converted = df[col].apply(parse_currency)
                if pd.api.types.is_numeric_dtype(converted):
                    df[col] = converted
                    audit['columns_converted'].append(f"{col}: Object -> Numeric (Currency)")
                    continue
            
            # Check if looks like datetime
            if sample_non_nulls and any(re.search(r'\d{2,4}[-/\.]\d{1,2}[-/\.]\d{1,2}', s) for s in sample_non_nulls):
                try:
                    df[col] = pd.to_datetime(df[col], errors='coerce', format='mixed')
                    audit['columns_converted'].append(f"{col}: Object -> Datetime")
                    continue
                except Exception:
                    pass
            
            # Impute missing strings with "Unknown" or mode
            if null_count > 0:
                mode_val = df[col].mode()[0] if not df[col].mode().empty else "Unknown"
                df[col] = df[col].fillna(mode_val)
        
        elif pd.api.types.is_numeric_dtype(df[col]):
            # Impute missing numeric with median
            if null_count > 0:
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
    
    # 5. Save cleaned CSV
    output_file_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_file_path, index=False)
    
    # 6. Save to SQLite table for SQL query execution
    conn = sqlite3.connect(str(DB_PATH))
    # Convert datetime objects to string ISO format for sqlite compatibility
    df_sql = df.copy()
    for col in df_sql.columns:
        if pd.api.types.is_datetime64_any_dtype(df_sql[col]):
            df_sql[col] = df_sql[col].dt.strftime('%Y-%m-%d')
            
    df_sql.to_sql(table_name, conn, if_exists='replace', index=False)
    conn.close()
    
    audit['final_rows'] = df.shape[0]
    audit['final_cols'] = df.shape[1]
    audit['column_types'] = {col: str(df[col].dtype) for col in df.columns}
    
    return df, audit
