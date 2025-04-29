import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from .config import Config
from .logger import AppLogger

logger = AppLogger.get_logger(__name__)

class DatabaseManager:
    """Handles all database operations"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_db()
        return cls._instance
    
    def _init_db(self):
        """Initialize database connection"""
        try:
            self.engine = create_engine(Config().database_url)
            self.Session = sessionmaker(bind=self.engine)
            logger.info("Database connection established")
        except Exception as e:
            logger.critical(f"Database connection failed: {str(e)}")
            raise
    
    def get_session(self):
        """Get a new database session"""
        return self.Session()
    
    def execute_query(self, query, params=None):
        """Execute raw SQL query safely"""
        session = self.get_session()
        try:
            result = session.execute(query, params or {})
            session.commit()
            return result
        except SQLAlchemyError as e:
            session.rollback()
            logger.error(f"Query failed: {str(e)}")
            raise
        finally:
            session.close()