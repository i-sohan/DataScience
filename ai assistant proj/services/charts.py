import plotly.express as px
import plotly.graph_objects as go
import json
import pandas as pd
import numpy as np

# Executive color palette
COLOR_PALETTE = ['#6366f1', '#10b981', '#f59e0b', '#ec4899', '#8b5cf6', '#3b82f6', '#06b6d4', '#14b8a6']

def auto_select_chart_type(df: pd.DataFrame) -> str:
    if df.empty or len(df.columns) < 2:
        return 'table'
        
    col_types = [df[c].dtype for c in df.columns]
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    
    # Check if first categorical column looks like date
    first_col_is_date = False
    if cat_cols:
        sample_str = str(df[cat_cols[0]].dropna().iloc[0]) if not df[cat_cols[0]].dropna().empty else ''
        if any(w in cat_cols[0].lower() for w in ['date', 'day', 'month', 'year', 'time']) or '-' in sample_str or '/' in sample_str:
            first_col_is_date = True
            
    if first_col_is_date and num_cols:
        return 'line'
    elif len(cat_cols) >= 1 and len(num_cols) >= 1:
        if df[cat_cols[0]].nunique() <= 6 and ('pct' in num_cols[0].lower() or 'share' in num_cols[0].lower() or 'ratio' in num_cols[0].lower()):
            return 'pie'
        return 'bar'
    elif len(num_cols) >= 2:
        return 'scatter'
    return 'bar'

def build_chart_json(df: pd.DataFrame, chart_type: str = 'auto', title: str = 'Chart Analytics', x_col: str = None, y_col: str = None) -> dict:
    if df.empty:
        return {}
        
    if chart_type == 'auto':
        chart_type = auto_select_chart_type(df)
        
    cols = df.columns.tolist()
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    
    x_var = x_col or (cat_cols[0] if cat_cols else cols[0])
    y_var = y_col or (num_cols[0] if num_cols else (cols[1] if len(cols) > 1 else cols[0]))
    
    fig = None
    
    if chart_type == 'bar':
        fig = px.bar(
            df, x=x_var, y=y_var,
            color=x_var if df[x_var].nunique() <= 10 else None,
            title=title,
            color_discrete_sequence=COLOR_PALETTE,
            template='plotly_dark'
        )
        fig.update_layout(bargap=0.25)
        
    elif chart_type == 'line':
        fig = px.line(
            df, x=x_var, y=y_var,
            markers=True,
            title=title,
            color_discrete_sequence=COLOR_PALETTE,
            template='plotly_dark'
        )
        
    elif chart_type == 'pie':
        fig = px.pie(
            df, names=x_var, values=y_var,
            title=title,
            color_discrete_sequence=COLOR_PALETTE,
            template='plotly_dark',
            hole=0.4
        )
        
    elif chart_type == 'scatter':
        size_var = num_cols[1] if len(num_cols) > 1 else None
        fig = px.scatter(
            df, x=x_var, y=y_var,
            size=size_var,
            color=cat_cols[0] if cat_cols else None,
            title=title,
            color_discrete_sequence=COLOR_PALETTE,
            template='plotly_dark'
        )
        
    elif chart_type == 'heatmap':
        if len(num_cols) >= 2:
            corr = df[num_cols].corr().round(2)
            fig = px.imshow(
                corr, text_auto=True,
                title=title or 'Correlation Heatmap',
                color_continuous_scale='Viridis',
                template='plotly_dark'
            )
        else:
            fig = px.bar(df, x=x_var, y=y_var, title=title, template='plotly_dark')
            
    elif chart_type == 'box':
        fig = px.box(
            df, x=x_var if cat_cols else None, y=y_var,
            points='all',
            title=title,
            color_discrete_sequence=COLOR_PALETTE,
            template='plotly_dark'
        )
    else:
        fig = px.bar(df, x=x_var, y=y_var, title=title, template='plotly_dark')

    # Apply modern glassmorphism executive layout styling
    fig.update_layout(
        paper_bgcolor='rgba(15, 23, 42, 0.6)',
        plot_bgcolor='rgba(15, 23, 42, 0.4)',
        font=dict(family='Inter, sans-serif', color='#f8fafc', size=13),
        title=dict(font=dict(size=18, color='#ffffff'), x=0.02),
        margin=dict(l=40, r=40, t=60, b=40),
        hoverlabel=dict(bgcolor='#1e293b', font_size=13, font_family='Inter')
    )
    
    return json.loads(fig.to_json())

def create_dashboard_charts(df: pd.DataFrame) -> dict:
    charts = {}
    cols = df.columns.tolist()
    num_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
    cat_cols = [c for c in df.columns if not pd.api.types.is_numeric_dtype(df[c])]
    
    # 1. Primary Breakdown (First categorical vs First numerical)
    if cat_cols and num_cols:
        cat = cat_cols[0]
        num = num_cols[0]
        agg_df = df.groupby(cat, as_index=False)[num].sum().sort_values(by=num, ascending=False).head(10)
        charts['primary_bar'] = build_chart_json(agg_df, chart_type='bar', title=f"Top {cat} by Total {num}")
        
        if len(agg_df) <= 7:
            charts['pie_chart'] = build_chart_json(agg_df, chart_type='pie', title=f"{cat} Breakdown ({num})")
            
    # 2. Secondary Breakdown (Second categorical vs Numerical or Secondary Numerical)
    if len(cat_cols) >= 2 and num_cols:
        cat2 = cat_cols[1]
        num = num_cols[0]
        agg_df2 = df.groupby(cat2, as_index=False)[num].sum().sort_values(by=num, ascending=False).head(8)
        charts['secondary_bar'] = build_chart_json(agg_df2, chart_type='bar', title=f"{cat2} Distribution")

    # 3. Correlation Heatmap
    if len(num_cols) >= 2:
        charts['correlation_heatmap'] = build_chart_json(df, chart_type='heatmap', title="Numerical Correlation Matrix")
        
    return charts
