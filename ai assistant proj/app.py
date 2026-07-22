import os
import json
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for

from config import UPLOAD_FOLDER, REPORT_FOLDER, DATASET_FOLDER, SECRET_KEY, MAX_CONTENT_LENGTH
from database.db import init_db, register_dataset, get_dataset, list_all_datasets, add_chat_message, get_chat_history
from services.cleaner import clean_dataset
from services.analyzer import profile_dataset, execute_sql_query
from services.llm import process_natural_language_question
from services.charts import create_dashboard_charts, build_chart_json
from services.forecaster import forecast_metric
from services.report_generator import generate_pdf_report

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# Initialize database tables on startup
init_db()

@app.route('/')
def index():
    datasets = list_all_datasets()
    return render_template('home.html', datasets=datasets)

@app.route('/api/datasets/load-sample', methods=['POST'])
def load_sample():
    data = request.get_json() or {}
    sample_key = data.get('sample', 'sales')
    
    sample_files = {
        'sales': DATASET_FOLDER / 'sample_sales.csv',
        'hr': DATASET_FOLDER / 'sample_hr.csv',
        'healthcare': DATASET_FOLDER / 'sample_healthcare.csv'
    }
    
    sample_path = sample_files.get(sample_key, DATASET_FOLDER / 'sample_sales.csv')
    if not sample_path.exists():
        return jsonify({'success': False, 'error': f"Sample file {sample_key} not found."}), 404
        
    dataset_id = f"sample_{sample_key}"
    table_name = f"table_{sample_key}"
    raw_path = sample_path
    cleaned_path = UPLOAD_FOLDER / f"cleaned_{sample_key}.csv"
    
    df_cleaned, audit = clean_dataset(raw_path, cleaned_path, table_name)
    summary_dict = profile_dataset(df_cleaned)
    summary_dict['audit'] = audit
    
    register_dataset(
        dataset_id=dataset_id,
        filename=sample_path.name,
        raw_path=raw_path,
        cleaned_path=cleaned_path,
        row_count=len(df_cleaned),
        col_count=len(df_cleaned.columns),
        summary_dict=summary_dict,
        table_name=table_name
    )
    
    return jsonify({'success': True, 'dataset_id': dataset_id})

@app.route('/api/datasets/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'No file uploaded'}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No selected file'}), 400
        
    filename = file.filename
    clean_fn = "".join([c if c.isalnum() or c in ['.', '_', '-'] else '_' for c in filename])
    dataset_id = f"ds_{Path(clean_fn).stem}_{int(os.times().elapsed)}"
    table_name = f"table_{int(os.times().elapsed)}"
    
    raw_path = UPLOAD_FOLDER / f"raw_{clean_fn}"
    cleaned_path = UPLOAD_FOLDER / f"cleaned_{clean_fn}.csv"
    file.save(raw_path)
    
    try:
        df_cleaned, audit = clean_dataset(raw_path, cleaned_path, table_name)
        summary_dict = profile_dataset(df_cleaned)
        summary_dict['audit'] = audit
        
        register_dataset(
            dataset_id=dataset_id,
            filename=filename,
            raw_path=raw_path,
            cleaned_path=cleaned_path,
            row_count=len(df_cleaned),
            col_count=len(df_cleaned.columns),
            summary_dict=summary_dict,
            table_name=table_name
        )
        
        return jsonify({'success': True, 'dataset_id': dataset_id})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/datasets/current')
def get_current_dataset():
    ds_id = request.args.get('id')
    if not ds_id:
        datasets = list_all_datasets()
        if datasets:
            ds_id = datasets[0]['id']
        else:
            return jsonify({'success': False, 'error': 'No datasets found.'})
            
    dataset = get_dataset(ds_id)
    if dataset:
        return jsonify({'success': True, 'dataset': dataset})
    return jsonify({'success': False, 'error': 'Dataset not found.'}), 404

@app.route('/profiling')
def profiling():
    datasets = list_all_datasets()
    if not datasets:
        return render_template('profiling.html', summary=None)
    ds_id = request.args.get('id') or datasets[0]['id']
    dataset = get_dataset(ds_id)
    summary = dataset.get('summary', {}) if dataset else None
    return render_template('profiling.html', summary=summary, dataset_info=dataset)

@app.route('/dashboard')
def dashboard():
    datasets = list_all_datasets()
    if not datasets:
        return redirect(url_for('index'))
    ds_id = request.args.get('id') or datasets[0]['id']
    dataset = get_dataset(ds_id)
    if not dataset:
        return redirect(url_for('index'))
        
    summary = dataset.get('summary', {})
    import pandas as pd
    df = pd.read_csv(dataset['cleaned_path'])
    charts = create_dashboard_charts(df)
    
    return render_template('dashboard.html', dataset_info=dataset, kpis=summary.get('kpis', {}), charts=charts)

@app.route('/chat')
def chat():
    datasets = list_all_datasets()
    if not datasets:
        return redirect(url_for('index'))
    ds_id = request.args.get('id') or datasets[0]['id']
    dataset = get_dataset(ds_id)
    history = get_chat_history(ds_id)
    return render_template('chat.html', dataset_info=dataset, history=history)

@app.route('/api/chat/ask', methods=['POST'])
def api_chat_ask():
    data = request.get_json() or {}
    dataset_id = data.get('dataset_id')
    user_query = data.get('query', '').strip()
    
    if not dataset_id or not user_query:
        return jsonify({'success': False, 'error': 'Missing dataset_id or user query.'}), 400
        
    dataset = get_dataset(dataset_id)
    if not dataset:
        return jsonify({'success': False, 'error': 'Dataset not found.'}), 404
        
    import pandas as pd
    df = pd.read_csv(dataset['cleaned_path'])
    table_name = dataset.get('table_name', 'data_table')
    
    # Process question with LLM / fallback
    res = process_natural_language_question(dataset_id, table_name, df, user_query)
    
    # Build chart if result has tabular data
    chart_spec = None
    records = res.get('query_result', {}).get('records', [])
    if records and len(records) > 0:
        res_df = pd.DataFrame(records)
        chart_spec = build_chart_json(res_df, title=f"Query Chart: {user_query}")
        
    # Save chat in DB
    add_chat_message(
        dataset_id=dataset_id,
        user_query=user_query,
        generated_code=res.get('sql'),
        result_data=records,
        answer_text=res.get('business_insight'),
        chart_json=chart_spec
    )
    
    return jsonify({
        'success': True,
        'user_query': user_query,
        'sql': res.get('sql'),
        'answer_text': res.get('business_insight'),
        'chart_spec': chart_spec
    })

@app.route('/forecasting')
def forecasting():
    datasets = list_all_datasets()
    if not datasets:
        return redirect(url_for('index'))
    ds_id = request.args.get('id') or datasets[0]['id']
    dataset = get_dataset(ds_id)
    summary = dataset.get('summary', {}) if dataset else {}
    return render_template('forecasting.html', dataset_info=dataset, summary=summary)

@app.route('/api/forecast/run', methods=['POST'])
def run_forecast_api():
    data = request.get_json() or {}
    dataset_id = data.get('dataset_id')
    metric_col = data.get('metric_col')
    date_col = data.get('date_col')
    periods = int(data.get('periods', 6))
    
    if not dataset_id or not metric_col or not date_col:
        return jsonify({'success': False, 'error': 'Missing parameters for forecasting.'}), 400
        
    dataset = get_dataset(dataset_id)
    if not dataset:
        return jsonify({'success': False, 'error': 'Dataset not found.'}), 404
        
    import pandas as pd
    df = pd.read_csv(dataset['cleaned_path'])
    res = forecast_metric(df, date_col=date_col, metric_col=metric_col, forecast_periods=periods)
    
    if 'error' in res:
        return jsonify({'success': False, 'error': res['error']}), 400
        
    return jsonify({'success': True, 'forecast': res})

@app.route('/api/reports/generate')
def generate_report():
    ds_id = request.args.get('dataset_id')
    if not ds_id:
        datasets = list_all_datasets()
        if datasets:
            ds_id = datasets[0]['id']
        else:
            return jsonify({'success': False, 'error': 'No dataset active.'}), 400
            
    dataset = get_dataset(ds_id)
    if not dataset:
        return jsonify({'success': False, 'error': 'Dataset not found.'}), 404
        
    history = get_chat_history(ds_id)
    summary = dataset.get('summary', {})
    
    try:
        pdf_path = generate_pdf_report(dataset, summary, history)
        download_url = f"/reports/download/{pdf_path.name}"
        return jsonify({'success': True, 'download_url': download_url})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/reports/download/<filename>')
def download_report_file(filename):
    return send_from_directory(REPORT_FOLDER, filename, as_attachment=True)

if __name__ == '__main__':
    print("Starting GenAI Business Analytics Assistant Flask Application...")
    app.run(host='127.0.0.1', port=5000, debug=True)
