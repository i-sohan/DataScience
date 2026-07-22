import pandas as pd
import numpy as np
import plotly.graph_objects as go
import json
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures

def forecast_metric(df: pd.DataFrame, date_col: str, metric_col: str, forecast_periods: int = 6) -> dict:
    if date_col not in df.columns or metric_col not in df.columns:
        return {'error': f"Columns {date_col} or {metric_col} not found in dataset."}
        
    # Copy & clean
    df_clean = df[[date_col, metric_col]].dropna().copy()
    df_clean[date_col] = pd.to_datetime(df_clean[date_col], errors='coerce')
    df_clean = df_clean.dropna().sort_values(by=date_col)
    
    if len(df_clean) < 5:
        return {'error': 'Insufficient date records for forecasting (minimum 5 time points required).'}
        
    # Resample to daily or monthly frequency
    df_clean.set_index(date_col, inplace=True)
    
    # Infer frequency
    days_range = (df_clean.index.max() - df_clean.index.min()).days
    if days_range > 180:
        resampled = df_clean.resample('ME').sum()
        freq_label = 'Months'
    elif days_range > 30:
        resampled = df_clean.resample('W').sum()
        freq_label = 'Weeks'
    else:
        resampled = df_clean.resample('D').sum()
        freq_label = 'Days'
        
    resampled = resampled.fillna(0)
    series = resampled[metric_col]
    
    n_points = len(series)
    x_hist = np.arange(n_points).reshape(-1, 1)
    y_hist = series.values
    
    # Fit Polynomial Ridge Model for robust trend + confidence interval
    poly = PolynomialFeatures(degree=min(2, max(1, n_points // 5)))
    x_poly = poly.fit_transform(x_hist)
    model = Ridge(alpha=1.0)
    model.fit(x_poly, y_hist)
    
    # Generate future points
    x_future = np.arange(n_points, n_points + forecast_periods).reshape(-1, 1)
    x_future_poly = poly.transform(x_future)
    y_future = model.predict(x_future_poly)
    y_future = np.maximum(y_future, 0) # Ensure non-negative forecast
    
    # Residual standard deviation for confidence interval
    y_pred_hist = model.predict(x_poly)
    residuals = y_hist - y_pred_hist
    std_error = np.std(residuals) if len(residuals) > 1 else np.mean(y_hist) * 0.1
    
    lower_bound = np.maximum(y_future - 1.96 * std_error, 0)
    upper_bound = y_future + 1.96 * std_error
    
    # Generate future dates
    last_date = series.index[-1]
    if freq_label == 'Months':
        future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=forecast_periods, freq='ME')
    elif freq_label == 'Weeks':
        future_dates = pd.date_range(start=last_date + pd.DateOffset(weeks=1), periods=forecast_periods, freq='W')
    else:
        future_dates = pd.date_range(start=last_date + pd.DateOffset(days=1), periods=forecast_periods, freq='D')

    # Construct Plotly Visualization
    fig = go.Figure()
    
    # Historical Trace
    fig.add_trace(go.Scatter(
        x=[d.strftime('%Y-%m-%d') for d in series.index],
        y=series.values,
        mode='lines+markers',
        name='Historical Actuals',
        line=dict(color='#6366f1', width=3),
        marker=dict(size=6)
    ))
    
    # Forecast Trace
    future_date_strs = [d.strftime('%Y-%m-%d') for d in future_dates]
    fig.add_trace(go.Scatter(
        x=future_date_strs,
        y=y_future.round(2),
        mode='lines+markers',
        name='AI Forecast',
        line=dict(color='#10b981', width=3, dash='dash'),
        marker=dict(size=8, symbol='diamond')
    ))
    
    # Confidence Interval Shading
    fig.add_trace(go.Scatter(
        x=future_date_strs + future_date_strs[::-1],
        y=np.concatenate([upper_bound.round(2), lower_bound.round(2)[::-1]]),
        fill='toself',
        fillcolor='rgba(16, 185, 129, 0.15)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        showlegend=True,
        name='95% Confidence Interval'
    ))
    
    fig.update_layout(
        title=f"Predictive {metric_col} Forecast ({forecast_periods} {freq_label} Ahead)",
        paper_bgcolor='rgba(15, 23, 42, 0.6)',
        plot_bgcolor='rgba(15, 23, 42, 0.4)',
        font=dict(family='Inter, sans-serif', color='#f8fafc', size=13),
        margin=dict(l=40, r=40, t=60, b=40),
        xaxis_title="Timeline",
        yaxis_title=metric_col,
        template='plotly_dark'
    )
    
    forecast_table = []
    for d, val, low, high in zip(future_date_strs, y_future, lower_bound, upper_bound):
        forecast_table.append({
            'period': d,
            'predicted_value': round(float(val), 2),
            'lower_bound': round(float(low), 2),
            'upper_bound': round(float(high), 2)
        })
        
    return {
        'metric': metric_col,
        'date_col': date_col,
        'freq_label': freq_label,
        'chart_spec': json.loads(fig.to_json()),
        'forecast_table': forecast_table,
        'total_predicted': round(float(np.sum(y_future)), 2),
        'expected_growth_pct': round(float(((y_future[-1] - series.values[-1]) / max(series.values[-1], 1)) * 100), 2)
    }
