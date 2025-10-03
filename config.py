import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Flask Settings
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')
    DEBUG = os.getenv('FLASK_DEBUG', 'False') == 'True'
    
    # API Keys
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    POLYGON_API_KEY = os.getenv('POLYGON_API_KEY')
    
    # Scheduling
    REFRESH_TIME = os.getenv('REFRESH_TIME', '08:00')
    TIMEZONE = os.getenv('TIMEZONE', 'Asia/Kolkata')
    
    # Database
    DATABASE_PATH = 'financial_news.db'
    
    # Scraping Settings
    REQUEST_TIMEOUT = 30
    MAX_RETRIES = 3
    RATE_LIMIT_DELAY = 2  # seconds between requests
    
    # AI Settings
    GEMINI_MODEL = 'gemini-2.0-flash-exp'
    MAX_ARTICLES_TO_SELECT = 7
    SUMMARY_MAX_WORDS = 500
    
    # History Settings
    HISTORY_DAYS = 7
    
    # Cache Settings
    CACHE_EXPIRY = 3600  # 1 hour in seconds
    
    # User Agent for scraping
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'