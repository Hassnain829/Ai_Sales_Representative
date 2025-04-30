from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from .utils.logger import AppLogger
from .utils.config import Config
from .models import db
from .routes import init_routes

logger = AppLogger.get_logger(__name__)

# Initialize extensions
db = SQLAlchemy()

def create_app(config_class=Config):
    """
    Application factory function that creates and configures the Flask app
    
    Args:
        config_class: Configuration class to use (defaults to Config)
    
    Returns:
        Flask: Configured Flask application instance
    """
    # Initialize Flask application
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Configure database URI
    app.config['SQLALCHEMY_DATABASE_URI'] = config_class().database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    try:
        # Initialize extensions
        db.init_app(app)
        
        # Register blueprints/routes
        init_routes(app)
        
        # Create database tables if they don't exist
        with app.app_context():
            db.create_all()
            logger.info("Database tables verified/created")
        
        # Register error handlers
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
        logger.warning(f"Bad request: {str(error)}")
        return {
            "error": "Bad request",
            "message": str(error)
        }, 400
    
    @app.errorhandler(404)
    def not_found(error):
        logger.warning(f"Not found: {str(error)}")
        return {
            "error": "Not found",
            "message": "The requested resource was not found"
        }, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {str(error)}")
        return {
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }, 500

# Import models after db initialization to avoid circular imports
from .models import Conversation, TrainingData