import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Centralized configuration management"""
    
    # Database
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", 5432)
    DB_NAME = os.getenv("DB_NAME", "sales_agent")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASS = os.getenv("DB_PASS", "123")
    
    # ML Models
    INTENT_MODEL = os.getenv("INTENT_MODEL", "facebook/bart-large-mnli")
    SENTIMENT_MODEL = os.getenv("SENTIMENT_MODEL", "distilbert-base-uncased-finetuned-sst-2-english")
    
    # Paths
    MODEL_DIR = os.getenv("MODEL_DIR", "data/models")
    TRAINING_DATA = os.getenv("TRAINING_DATA", "data/training/labeled.csv")
    
    @property
    def database_url(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"