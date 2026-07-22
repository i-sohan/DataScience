import pandas as pd
import numpy as np
import sqlite3
import json
from config import DB_PATH

def profile_dataset(df: pd.DataFrame) -> dict:
    total_rows = len(df)
    total_cols = len(df.columns)
    
    col_profiles = []
    numeric_cols = []
    categorical_cols = []
    datetime_cols = []
    
    for col in df.columns:
        dtype_str = str(df[col].dtype)
        null_cnt = int(df[col].isna().sum())
        null_pct = round((null_cnt / total_rows) * 100, 2) if total_rows > 0 else 0.0
        unique_cnt = int(df[col].nunique())
        
        prof = {
            'column': col,
            'dtype': dtype_str,
            'null_count': null_cnt,
            'null_pct': null_pct,
            'unique_count': unique_cnt,
            'sample_values': [str(x) for x in df[col].dropna().head(5).tolist()]
        }
        
        if pd.api.types.is_numeric_dtype(df[col]):
            numeric_cols.append(col)
            series = df[col].dropna()
            if not series.empty:
                q1 = float(series.quantile(0.25))
                q3 = float(series.quantile(0.75))
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                outliers_cnt = int(((series < lower_bound) | (series > upper_bound)).sum())
                
                prof.update({
                    'min': float(series.min()),
                    'max': float(series.max()),
                    'mean': round(float(series.mean()), 2),
                    'std': round(float(series.std()), 2) if len(series) > 1 else 0.0,
                    'median': round(float(series.median()), 2),
                    'q1': round(q1, 2),
                    'q3': round(q3, 2),
                    'iqr': round(iqr, 2),
                    'outliers_count': outliers_cnt
                })
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            datetime_cols.append(col)
            series = df[col].dropna()
            if not series.empty:
                prof.update({
                    'min_date': str(series.min()),
                    'max_date': str(series.max())
                })
        else:
            categorical_cols.append(col)
            top_vals = df[col].value_counts().head(5).to_dict()
            prof['top_frequencies'] = {str(k): int(v) for k, v in top_vals.items()}
            
        col_profiles.append(prof)
        
    # Correlation Matrix for Numeric Columns
    correlation_matrix = {}
    if len(numeric_cols) > 1:
        corr_df = df[numeric_cols].corr().round(2).fillna(0)
        correlation_matrix = corr_df.to_dict()
        
    # Overall KPI Summary metrics detection (e.g. Sales, Profit, Revenue, Orders, Income, Charges)
    kpis = {}
    for col in numeric_cols:
        col_lower = col.lower()
        if any(kw in col_lower for kw in ['sales', 'revenue', 'profit', 'income', 'charges', 'price']):
            kpis[col] = {
                'total': round(float(df[col].sum()), 2),
                'average': round(float(df[col].mean()), 2),
                'max': round(float(df[col].max()), 2)
            }
            
    return {
        'total_rows': total_rows,
        'total_cols': total_cols,
        'numeric_columns': numeric_cols,
        'categorical_columns': categorical_cols,
        'datetime_columns': datetime_cols,
        'columns': col_profiles,
        'correlation_matrix': correlation_matrix,
        'kpis': kpis
    }

def execute_sql_query(query_str: str, table_name: str) -> dict:
    conn = sqlite3.connect(str(DB_PATH))
    try:
        # Basic sanitization
        query_str_clean = query_str.strip()
        if not query_str_clean.lower().startswith('select') and not query_str_clean.lower().startswith('with'):
            return {'error': 'Only SELECT or CTE queries are allowed for safety.'}
            
        df_res = pd.read_sql_query(query_str_clean, conn)
        conn.close()
        
        # Replace NaNs
        df_res = df_res.fillna('')
        
        return {
            'success': True,
            'row_count': len(df_res),
            'columns': df_res.columns.tolist(),
            'records': df_res.to_dict(orient='records'),
            'preview_markdown': df_res.head(10).to_markdown()
        }
    except Exception as e:
        conn.close()
        return {
            'success': False,
            'error': str(e)
        }

def execute_pandas_query(df: pd.DataFrame, pandas_code: str) -> dict:
    try:
        local_vars = {'df': df, 'pd': pd, 'np': np}
        # Execute code securely
        exec_code = f"result = {pandas_code.strip()}" if '\n' not in pandas_code and not pandas_code.startswith('result =') else pandas_code
        exec(exec_code, {}, local_vars)
        result = local_vars.get('result')
        
        if isinstance(result, pd.DataFrame):
            res_df = result.fillna('')
            return {
                'success': True,
                'type': 'dataframe',
                'columns': res_df.columns.tolist(),
                'records': res_df.to_dict(orient='records')
            }
        elif isinstance(result, pd.Series):
            res_df = result.reset_index().fillna('')
            return {
                'success': True,
                'type': 'series',
                'columns': res_df.columns.tolist(),
                'records': res_df.to_dict(orient='records')
            }
        else:
            return {
                'success': True,
                'type': 'scalar',
                'value': str(result)
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
