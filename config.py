import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('postgresql://postgres:123@localhost/sales_agent')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
     # Correct way to set up Twilio credentials
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID', 'AC3b33ee1708fe8dd88ed7356b4867b515')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN','aaf1c66c46b44e7ef8577882e6065f77')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER','+14234828390')
    
    # ML Models
    INTENT_MODEL_PATH = os.getenv('INTENT_MODEL_PATH', 'data/models/intent_classifier')
    SENTIMENT_MODEL_PATH = os.getenv('SENTIMENT_MODEL_PATH', 'data/models/sentiment')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/sales_agent.log')