from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .utils.logger import AppLogger
from dotenv import load_dotenv
from config import Config

# Initialize extensions
db = SQLAlchemy()
load_dotenv()  # Load environment variables

logger = AppLogger.get_logger(__name__)

def create_app(config_class=Config):
    """Application factory function"""
    app = Flask(__name__, template_folder='templates')
    
    try:
        # Load configuration
        app.config.from_object(config_class)
        
        # Initialize extensions
        db.init_app(app)
        
        # No need to add extra handlers — AppLogger has already configured console + file + JSON logging
        
        with app.app_context():
            # Validate configuration
            missing = [key for key in [
                'SQLALCHEMY_DATABASE_URI',
                'TWILIO_ACCOUNT_SID',
                'TWILIO_AUTH_TOKEN'
            ] if not app.config.get(key)]
            
            if missing:
                raise ValueError(f"Missing configuration: {', '.join(missing)}")
            
            # Create database tables
            db.create_all()
            logger.info("Database tables initialized")

            # Register routes and error handlers
            from .routes import init_routes
            init_routes(app)
            _register_error_handlers(app)

        logger.info("Application initialized successfully")
        return app

    except Exception as e:
        logger.critical(f"Failed to initialize application: {str(e)}")
        raise
    
def _register_error_handlers(app):
    """Register custom error handlers for the application"""
    
    @app.errorhandler(400)
    def bad_request(error):
        logger.warning(f"Bad request: {error}")
        return {"error": "Bad request", "message": str(error)}, 400
    
    @app.errorhandler(404)
    def not_found(error):
        logger.warning(f"Not found: {error}")
        return {"error": "Not found", "message": "The requested resource was not found"}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return {"error": "Internal server error", "message": "An unexpected error occurred"}, 500

# Import models after db initialization to avoid circular imports
from .models import Conversation, TrainingData
