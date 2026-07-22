import sqlite3
import json
from datetime import datetime
from pathlib import Path
from config import DB_PATH

def get_db_connection():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Table for Datasets metadata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS datasets (
            id TEXT PRIMARY KEY,
            filename TEXT NOT NULL,
            raw_path TEXT NOT NULL,
            cleaned_path TEXT NOT NULL,
            row_count INTEGER,
            col_count INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            summary_json TEXT,
            table_name TEXT
        )
    ''')
    
    # Table for Chat and Query Logs
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_id TEXT NOT NULL,
            user_query TEXT NOT NULL,
            generated_code TEXT,
            result_json TEXT,
            answer_text TEXT,
            chart_json TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (dataset_id) REFERENCES datasets(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def register_dataset(dataset_id, filename, raw_path, cleaned_path, row_count, col_count, summary_dict, table_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO datasets (id, filename, raw_path, cleaned_path, row_count, col_count, summary_json, table_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        dataset_id,
        filename,
        str(raw_path),
        str(cleaned_path),
        row_count,
        col_count,
        json.dumps(summary_dict),
        table_name
    ))
    conn.commit()
    conn.close()

def get_dataset(dataset_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM datasets WHERE id = ?', (dataset_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        data = dict(row)
        if data.get('summary_json'):
            data['summary'] = json.loads(data['summary_json'])
        return data
    return None

def list_all_datasets():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, filename, row_count, col_count, created_at, table_name FROM datasets ORDER BY created_at DESC')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_chat_message(dataset_id, user_query, generated_code, result_data, answer_text, chart_json=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO chat_history (dataset_id, user_query, generated_code, result_json, answer_text, chart_json)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        dataset_id,
        user_query,
        generated_code,
        json.dumps(result_data) if result_data else None,
        answer_text,
        json.dumps(chart_json) if chart_json else None
    ))
    conn.commit()
    conn.close()

def get_chat_history(dataset_id, limit=20):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, user_query, generated_code, result_json, answer_text, chart_json, timestamp
        FROM chat_history
        WHERE dataset_id = ?
        ORDER BY id ASC
        LIMIT ?
    ''', (dataset_id, limit))
    rows = cursor.fetchall()
    conn.close()
    history = []
    for r in rows:
        item = dict(r)
        if item.get('result_json'):
            item['result_data'] = json.loads(item['result_json'])
        if item.get('chart_json'):
            item['chart_spec'] = json.loads(item['chart_json'])
        history.append(item)
    return history
