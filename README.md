# 📊 GenAI Business Analytics Assistant

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/framework-Flask%203.0%2B-green.svg)](https://flask.palletsprojects.com/)
[![LLM Powered](https://img.shields.io/badge/AI-Gemini%20%7C%20OpenAI-orange.svg)](https://deepmind.google/technologies/gemini/)
[![License](https://img.shields.io/badge/license-MIT-purple.svg)](LICENSE)

An enterprise-grade, full-stack **AI-Powered Business Intelligence & Data Analytics Assistant** built with **Python, Flask, SQLite, Pandas, Plotly, Scikit-Learn**, and **Generative AI (Google Gemini & OpenAI)**. 

This application empowers business users, data analysts, and decision-makers to upload raw structured datasets (CSV, Excel), automatically clean and profile data, generate interactive dashboards, query data using natural language (Text-to-SQL), perform predictive time-series forecasting, and export executive PDF reports.

---

## 🌟 Key Features

### 🧹 1. Automated Data Cleaning & Ingestion Engine
- **Multi-Format Support**: Upload `.csv`, `.xlsx`, and `.xls` files or load built-in domain-specific sample datasets (Sales, HR, Healthcare).
- **Auto-Imputation**: Intelligently fills missing numeric values using column medians and categorical values with mode values.
- **Data Standardization**: Auto-strips currency symbols (e.g., `₹50,000` $\rightarrow$ `50000.0`), normalizes column names into SQL-compliant identifiers, trims whitespace, and formats date columns.
- **Audit Logging**: Generates detailed audit metrics for missing value imputation, string cleanup, and duplicate row removals.

### 📈 2. Automated Exploratory Data Analysis (EDA) & Profiling
- **Statistical Summary**: Displays mean, median, standard deviation, min/max, skewness, and missing rate metrics for every column.
- **Dataset Health Check**: Calculates completeness scores, data type distributions, unique value counts, and memory usage.
- **Dynamic KPIs**: Automatically computes top-level key performance indicators (Total Revenue/Sales, Record Counts, Averages).

### 💬 3. AI-Powered Natural Language Chat (Text-to-SQL)
- **Natural Language Querying**: Ask complex analytical questions in plain English (e.g., *"What are the top 5 states by total sales?"* or *"Which department has the highest attrition rate?"*).
- **LLM Integration**: Supports **Google Gemini 1.5 Flash** and **OpenAI GPT-4o-mini** to translate natural language into optimized SQLite queries.
- **Offline Rule-Based Fallback**: Built-in intelligent SQL parser and narrative generator that works seamlessly even without API keys for standard business queries.
- **Automated Insights**: Translates query result tables into actionable business summaries with auto-generated chart visualizations.

### 📊 4. Interactive Dashboards & Plotly Visualizations
- **Auto-Generated Charts**: Renders distribution plots, categorical bar charts, correlation heatmaps, numerical scatter plots, and box plots.
- **Interactive Controls**: Powered by **Plotly.js** with zoom, pan, hover tooltips, and image export capabilities.

### 🔮 5. Predictive Time-Series Forecasting
- **Machine Learning Engine**: Employs **Ridge Polynomial Regression** and **Holt-Winters Exponential Smoothing** to project future metrics.
- **Adaptive Frequency Resampling**: Automatically detects daily, weekly, or monthly time frequencies.
- **Confidence Bounds**: Calculates 95% confidence interval bounds for future metric trajectories.

### 📄 6. Executive PDF Report Generation
- **One-Click Export**: Generates publication-ready PDF reports using **ReportLab**.
- **Comprehensive Structure**: Includes Executive Summary, Audit Metrics, Statistical Summaries, Top KPIs, and AI Chat Q&A history.

---

## 🏗️ Architecture & Tech Stack

### Technology Stack
- **Backend Framework**: Python 3.10+, Flask 3.0+
- **Data Engineering**: Pandas, NumPy, Statsmodels, Scikit-Learn
- **Database**: SQLite3
- **Generative AI**: Google Gemini 1.5 Flash API, OpenAI GPT-4o-mini API
- **Data Visualization**: Plotly Python API, Plotly.js
- **Report Generation**: ReportLab
- **Frontend UI**: HTML5, Vanilla CSS3 (Glassmorphism design system), JavaScript (ES6+, Fetch API)

### Project Directory Structure
```text
ai assistant proj/
├── app.py                     # Main Flask Application Router & API Endpoints
├── config.py                  # App Configuration & Path Constants
├── generate_samples.py        # Synthetic Sample Dataset Generator Script
├── requirements.txt           # Python Package Dependencies
├── database/
│   ├── analytics.db           # SQLite Database (Metadata, Chat Logs, Cleaned Tables)
│   └── db.py                  # Database Schema, Initialization & CRUD Helpers
├── datasets/                  # Sample CSV Datasets Storage
│   ├── sample_sales.csv       # E-Commerce Sales dataset (1,000 records)
│   ├── sample_hr.csv          # HR Attrition dataset (500 records)
│   └── sample_healthcare.csv  # Healthcare Patient Diagnostics dataset (500 records)
├── reports/                   # Generated Executive PDF Reports Output Directory
├── services/                  # Core Business Logic & AI Services
│   ├── analyzer.py            # EDA Profiling & SQL Query Executor
│   ├── charts.py              # Dynamic Plotly Visualization Generators
│   ├── cleaner.py             # Data Ingestion, Auto-Cleaner & Audit Logger
│   ├── forecaster.py          # Predictive Forecasting Engine
│   ├── llm.py                 # LLM Text-to-SQL & Fallback Parser Engine
│   └── report_generator.py    # ReportLab PDF Generator Module
├── static/                    # CSS Stylesheets, JavaScript Libraries & Assets
├── templates/                 # Jinja2 HTML Templates
│   ├── base.html              # Core Layout & Navigation Header
│   ├── home.html              # Dataset Upload & Sample Loader Page
│   ├── profiling.html         # Data Profiling & Statistical EDA Page
│   ├── dashboard.html         # Interactive Plotly Dashboard Page
│   ├── chat.html              # AI Natural Language Analyst Chat Page
│   └── forecasting.html       # Predictive Forecasting Page
├── test_app.py                # Integration & API Tests
└── uploads/                   # Temporary Raw & Cleaned Data Files
```

---

## 🚀 Quick Start & Installation

### Prerequisites
- Python 3.10 or higher
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/genai-business-analytics-assistant.git
cd "genai-business-analytics-assistant/ai assistant proj"
```

### 2. Create and Activate a Virtual Environment
- **Windows (PowerShell)**:
  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1
  ```
- **macOS / Linux**:
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. (Optional) Configure Environment Variables
Create a `.env` file in the project root directory or export your API keys:

```env
# Optional LLM API Keys (App will fallback to local rule-based engine if omitted)
GEMINI_API_KEY="your-google-gemini-api-key"
OPENAI_API_KEY="your-openai-api-key"

# Flask Configuration
SECRET_KEY="your-custom-secret-key"
DEFAULT_MODEL="gemini-1.5-flash"
```

### 5. Generate Sample Datasets
Run the sample generator script to generate synthetic datasets for testing:
```bash
python generate_samples.py
```

### 6. Launch the Application
```bash
python app.py
```
Open your browser and navigate to **`http://127.0.0.1:5000`**.

---

## 🔌 API Reference Overview

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `GET /` | `GET` | Home page & dataset upload interface |
| `POST /api/datasets/upload` | `POST` | Upload custom CSV or Excel file |
| `POST /api/datasets/load-sample` | `POST` | Load pre-packaged sample dataset (`sales`, `hr`, `healthcare`) |
| `GET /api/datasets/current` | `GET` | Retrieve metadata of currently active dataset |
| `GET /profiling` | `GET` | View statistical EDA profiling metrics |
| `GET /dashboard` | `GET` | View interactive Plotly charts & KPIs |
| `GET /chat` | `GET` | AI Natural Language Chat interface |
| `POST /api/chat/ask` | `POST` | Submit natural language query (returns SQL, business summary, and chart) |
| `GET /forecasting` | `GET` | View forecasting dashboard |
| `POST /api/forecast/run` | `POST` | Execute time-series forecast for selected date and metric columns |
| `GET /api/reports/generate` | `GET` | Generate executive PDF report |
| `GET /reports/download/<filename>` | `GET` | Download generated PDF report |

---

## 🧪 Testing

To run the unit and integration test suite:
```bash
python -m unittest test_app.py
```

---

## 🛡️ Security & Safety Features
- **SQL Injection Prevention**: User-generated SQL commands are strictly sanitized. Write operations (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`) are blocked; only read-only `SELECT` queries are permitted.
- **Safe File Handling**: File names are sanitized before storage, avoiding directory traversal risks.
- **Local SQLite Processing**: Sensitive financial or personal data stays stored locally within your SQLite instance.

---

## 🤝 Contributing

Contributions are welcome! Follow these steps to contribute:
1. Fork the repository.
2. Create a new feature branch (`git checkout -b feature/AmazingFeature`).
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
4. Push to the branch (`git push origin feature/AmazingFeature`).
5. Open a Pull Request.

---

## 📜 License

Distributed under the **MIT License**. See `LICENSE` for details.

---

## ✉️ Contact & Acknowledgments

- **Author**: Sohan
- **Built with**: Python, Flask, Google Gemini, OpenAI, Plotly, Pandas & SQLite.
