import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Directory setup
UPLOAD_FOLDER = BASE_DIR / 'uploads'
REPORT_FOLDER = BASE_DIR / 'reports'
DATASET_FOLDER = BASE_DIR / 'datasets'
DB_PATH = BASE_DIR / 'database' / 'analytics.db'

# Ensure directories exist
UPLOAD_FOLDER.mkdir(exist_ok=True)
REPORT_FOLDER.mkdir(exist_ok=True)
DATASET_FOLDER.mkdir(exist_ok=True)
(BASE_DIR / 'database').mkdir(exist_ok=True)

# Secret Key & Flask Config
SECRET_KEY = os.environ.get('SECRET_KEY', 'genai-business-analytics-secret-key-2026')
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB max upload limit

# LLM API Keys
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
DEFAULT_MODEL = os.environ.get('DEFAULT_MODEL', 'gemini-1.5-flash')
