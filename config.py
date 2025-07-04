import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

class Config:
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')  # Must match .env
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
     # Correct way to set up Twilio credentials
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')
    
    # ML Models
    INTENT_MODEL_PATH = os.getenv('INTENT_MODEL_PATH', 'data/models/intent_classifier')
    SENTIMENT_MODEL_PATH = os.getenv('SENTIMENT_MODEL_PATH', 'data/models/sentiment')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/sales_agent.log')
