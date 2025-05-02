import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables

class Config:
    # Database Configuration
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')  # Must match .env
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Twilio Configuration
    TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
    TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
    TWILIO_PHONE_NUMBER = os.getenv('TWILIO_PHONE_NUMBER')

    # Validate configuration on load
    def __init__(self):
        self._validate()
        
    def _validate(self):
        """Ensure required configuration exists"""
        required = {
            'SQLALCHEMY_DATABASE_URI': self.SQLALCHEMY_DATABASE_URI,
            'TWILIO_ACCOUNT_SID': self.TWILIO_ACCOUNT_SID,
            'TWILIO_AUTH_TOKEN': self.TWILIO_AUTH_TOKEN
        }
        missing = [k for k, v in required.items() if not v]
        if missing:
            raise ValueError(f"Missing configuration for: {', '.join(missing)}")