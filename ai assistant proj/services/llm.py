import os
import json
import re
import requests
import pandas as pd
from services.analyzer import execute_sql_query
from config import GEMINI_API_KEY, OPENAI_API_KEY

def call_gemini_api(prompt: str, api_key: str = None) -> str:
    key = api_key or GEMINI_API_KEY or os.environ.get('GEMINI_API_KEY', '')
    if not key:
        raise ValueError("No Gemini API key available.")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={key}"
    headers = {'Content-Type': 'application/json'}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=15)
    if resp.status_code == 200:
        data = resp.json()
        return data['candidates'][0]['content']['parts'][0]['text']
    else:
        raise RuntimeError(f"Gemini API call failed with code {resp.status_code}: {resp.text}")

def call_openai_api(prompt: str, api_key: str = None) -> str:
    key = api_key or OPENAI_API_KEY or os.environ.get('OPENAI_API_KEY', '')
    if not key:
        raise ValueError("No OpenAI API key available.")
    
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f"Bearer {key}"
    }
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2
    }
    resp = requests.post(url, json=payload, headers=headers, timeout=15)
    if resp.status_code == 200:
        return resp.json()['choices'][0]['message']['content']
    else:
        raise RuntimeError(f"OpenAI API call failed: {resp.text}")

def rule_based_fallback_sql(user_query: str, table_name: str, df: pd.DataFrame) -> tuple[str, str]:
    """
    Fallback NLP parser when API key is missing. Generates SQL and narrative insight.
    """
    q = user_query.lower()
    cols = df.columns.tolist()
    cols_lower = [c.lower() for c in cols]
    
    # 1. State / Region Revenue & Sales breakdown
    if ('state' in q or 'region' in q or 'city' in q) and any(k in q for k in ['revenue', 'sales', 'profit', 'highest', 'top']):
        group_col = 'State' if 'State' in cols else ('City' if 'City' in cols else cols[0])
        val_col = 'Sales' if 'Sales' in cols else ('Profit' if 'Profit' in cols else 'HospitalCharges')
        
        sql = f"SELECT {group_col}, SUM({val_col}) AS Total_{val_col}, COUNT(*) AS Total_Orders FROM {table_name} GROUP BY {group_col} ORDER BY Total_{val_col} DESC LIMIT 10;"
        return sql, f"Grouped by {group_col} and calculated total {val_col} sorted in descending order."

    # 2. Product / Category breakdown
    if any(k in q for k in ['product', 'category', 'item']) and any(k in q for k in ['profit', 'sales', 'revenue', 'highest', 'top', 'discontinue']):
        group_col = 'Product' if 'Product' in cols else ('Category' if 'Category' in cols else cols[0])
        val_col = 'Profit' if 'Profit' in cols and 'profit' in q else ('Sales' if 'Sales' in cols else 'Quantity')
        
        order_dir = "ASC" if "discontinue" in q or "lowest" in q or "worst" in q else "DESC"
        sql = f"SELECT {group_col}, SUM({val_col}) AS Total_{val_col}, SUM(Quantity) AS Total_Qty FROM {table_name} GROUP BY {group_col} ORDER BY Total_{val_col} {order_dir} LIMIT 10;"
        return sql, f"Aggregated {group_col} by {val_col} to analyze performance."

    # 3. Department / HR Attrition Analysis
    if ('department' in q or 'attrition' in q or 'employee' in q or 'leave' in q) and 'Department' in cols:
        val_col = 'Attrition' if 'Attrition' in cols else 'MonthlyIncome'
        if 'Attrition' in cols:
            sql = f"SELECT Department, COUNT(*) AS Total_Employees, SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END) AS Attrition_Count, ROUND(100.0 * SUM(CASE WHEN Attrition = 'Yes' THEN 1 ELSE 0 END) / COUNT(*), 2) AS Attrition_Rate_Pct FROM {table_name} GROUP BY Department ORDER BY Attrition_Rate_Pct DESC;"
        else:
            sql = f"SELECT Department, COUNT(*) AS Employee_Count, AVG(MonthlyIncome) AS Avg_Income FROM {table_name} GROUP BY Department ORDER BY Employee_Count DESC;"
        return sql, "Calculated employee count and attrition rates per department."

    # 4. Diabetes Risk / Patient Age Group Analysis
    if ('diabetes' in q or 'risk' in q or 'patient' in q or 'age' in q) and ('GlucoseLevel' in cols or 'DiabetesRisk' in cols or 'Age' in cols):
        if 'DiabetesRisk' in cols:
            sql = f"SELECT DiabetesRisk, COUNT(*) AS Patient_Count, ROUND(AVG(Age), 1) AS Avg_Age, ROUND(AVG(GlucoseLevel), 1) AS Avg_Glucose, ROUND(AVG(BMI), 1) AS Avg_BMI FROM {table_name} GROUP BY DiabetesRisk ORDER BY Patient_Count DESC;"
        elif 'Age' in cols:
            sql = f"SELECT CASE WHEN Age < 30 THEN '18-29' WHEN Age BETWEEN 30 AND 50 THEN '30-50' ELSE '50+' END AS Age_Group, COUNT(*) AS Patient_Count, ROUND(AVG(GlucoseLevel), 1) AS Avg_Glucose FROM {table_name} GROUP BY Age_Group ORDER BY Patient_Count DESC;"
        else:
            sql = f"SELECT * FROM {table_name} LIMIT 10;"
        return sql, "Analyzed patient demographics and health metrics."

    # 5. Top customers / General Top N query
    if 'customer' in q or 'top' in q:
        group_col = 'Customer' if 'Customer' in cols else cols[0]
        val_col = 'Sales' if 'Sales' in cols else ('Profit' if 'Profit' in cols else cols[1])
        sql = f"SELECT {group_col}, SUM({val_col}) AS Total_Value FROM {table_name} GROUP BY {group_col} ORDER BY Total_Value DESC LIMIT 10;"
        return sql, f"Extracted top 10 {group_col} entries by {val_col}."

    # Default general SQL query
    num_cols = [c for c in cols if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c for c in cols if not pd.api.types.is_numeric_dtype(df[c])]
    
    if cat_cols and num_cols:
        g = cat_cols[0]
        v = num_cols[0]
        sql = f"SELECT {g}, SUM({v}) AS Total_{v}, AVG({v}) AS Avg_{v} FROM {table_name} GROUP BY {g} ORDER BY Total_{v} DESC LIMIT 10;"
    else:
        sql = f"SELECT * FROM {table_name} LIMIT 10;"
    return sql, "Executed group aggregation."

def process_natural_language_question(dataset_id: str, table_name: str, df: pd.DataFrame, user_query: str, api_key: str = None, provider: str = 'auto') -> dict:
    table_schema = {col: str(df[col].dtype) for col in df.columns}
    sample_rows = df.head(3).to_dict(orient='records')
    
    generated_sql = ""
    business_insight = ""
    query_result = None
    
    # Try LLM APIs if available, otherwise rule-based fallback
    prompt_sql = f"""
You are a Lead Data Analyst & SQL Expert.
Database Table Name: `{table_name}`
Table Schema (Column: DataType): {json.dumps(table_schema)}
Sample Data Rows: {json.dumps(sample_rows, default=str)}

User Question: "{user_query}"

Task:
1. Write a valid SQLite SELECT query to answer the user's question accurately.
2. Return ONLY the raw SQL query inside ```sql ... ``` code blocks. Do not add markdown text outside the code block.
"""

    llm_success = False
    
    if provider in ['gemini', 'auto'] and (api_key or GEMINI_API_KEY or os.environ.get('GEMINI_API_KEY')):
        try:
            raw_response = call_gemini_api(prompt_sql, api_key)
            match = re.search(r'```sql\s*(.*?)\s*```', raw_response, re.DOTALL)
            generated_sql = match.group(1).strip() if match else raw_response.strip()
            llm_success = True
        except Exception as e:
            print(f"Gemini API attempt failed: {e}")
            
    if not llm_success and provider in ['openai', 'auto'] and (api_key or OPENAI_API_KEY or os.environ.get('OPENAI_API_KEY')):
        try:
            raw_response = call_openai_api(prompt_sql, api_key)
            match = re.search(r'```sql\s*(.*?)\s*```', raw_response, re.DOTALL)
            generated_sql = match.group(1).strip() if match else raw_response.strip()
            llm_success = True
        except Exception as e:
            print(f"OpenAI API attempt failed: {e}")

    if not llm_success:
        # Use Rule-Based Analytical Fallback
        generated_sql, _ = rule_based_fallback_sql(user_query, table_name, df)
        
    # Execute SQL
    query_result = execute_sql_query(generated_sql, table_name)
    
    if not query_result.get('success'):
        # Fallback to simple select if query errored
        generated_sql = f"SELECT * FROM {table_name} LIMIT 10;"
        query_result = execute_sql_query(generated_sql, table_name)

    # Generate Executive Business Narrative
    result_data = query_result.get('records', [])
    
    prompt_insight = f"""
You are an Executive Business Intelligence Director.
User Question: "{user_query}"
SQL Executed: `{generated_sql}`
QueryResult Data (JSON): {json.dumps(result_data[:10], default=str)}

Task:
Write a concise, professional executive response in Markdown format:
1. Directly answer the question with exact figures (e.g. "Karnataka generated ₹5.8 Cr, which is 23% higher than Maharashtra").
2. Highlight key takeaways and comparison percentages.
3. Provide 2 actionable business recommendations based on this result.
Keep it bulleted, executive-friendly, and engaging.
"""

    if llm_success:
        try:
            if provider == 'openai':
                business_insight = call_openai_api(prompt_insight, api_key)
            else:
                business_insight = call_gemini_api(prompt_insight, api_key)
        except Exception:
            business_insight = generate_fallback_insight(user_query, result_data)
    else:
        business_insight = generate_fallback_insight(user_query, result_data)
        
    return {
        'user_query': user_query,
        'sql': generated_sql,
        'query_result': query_result,
        'business_insight': business_insight
    }

def generate_fallback_insight(user_query: str, records: list) -> str:
    if not records:
        return f"**Analysis Summary for '{user_query}'**:\n- No matching data records were found for this query parameters."
    
    first = records[0]
    keys = list(first.keys())
    
    dim_key = keys[0]
    val_key = keys[1] if len(keys) > 1 else keys[0]
    
    val_1 = first[val_key]
    val_1_fmt = f"₹{val_1:,.2f}" if isinstance(val_1, (int, float)) and val_1 > 1000 else str(val_1)
    
    text = f"### 📊 Business Insight Summary\n\n"
    text += f"**Key Finding**: **{first[dim_key]}** recorded the top rank for **{val_key}** with a value of **{val_1_fmt}**.\n\n"
    
    if len(records) > 1:
        second = records[1]
        val_2 = second[val_key]
        val_2_fmt = f"₹{val_2:,.2f}" if isinstance(val_2, (int, float)) and val_2 > 1000 else str(val_2)
        text += f"- **Runner Up**: **{second[dim_key]}** followed with **{val_2_fmt}**.\n"
        if isinstance(val_1, (int, float)) and isinstance(val_2, (int, float)) and val_2 > 0:
            diff_pct = round(((val_1 - val_2) / val_2) * 100, 1)
            text += f"- **Comparison**: Top performer **{first[dim_key]}** exceeded **{second[dim_key]}** by **{diff_pct}%**.\n"
            
    text += f"\n#### 💡 Actionable Business Recommendations:\n"
    text += f"1. **Capitalize on Growth**: Focus marketing and resource allocation towards **{first[dim_key]}** to sustain momentum.\n"
    text += f"2. **Operational Optimization**: Investigate performance drivers in top segments to replicate success across lower performing categories.\n"
    
    return text
