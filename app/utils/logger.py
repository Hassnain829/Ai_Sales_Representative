import logging
import sys
import os
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from datetime import datetime
import json
from typing import Dict, Any

class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs in JSON format"""
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.threadName
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

class AppLogger:
    """Centralized logging management with multiple handlers"""
    
    _loggers: Dict[str, logging.Logger] = {}
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get or create a configured logger instance"""
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            logger.setLevel(logging.DEBUG)
            
            os.makedirs("logs", exist_ok=True)
            
            # 1. Console Handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            logger.addHandler(console_handler)
            
            # 2. File Handler (rotating by size, delayed open)
            file_handler = RotatingFileHandler(
                'logs/app.log',
                maxBytes=10_000_000,
                backupCount=5,
                encoding='utf-8',
                delay=True
            )
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            logger.addHandler(file_handler)
            
            # 3. JSON Handler (daily rotation)
            json_handler = TimedRotatingFileHandler(
                filename="logs/structured.json",
                when='midnight',
                backupCount=7,
                encoding='utf-8'
            )
            json_handler.setFormatter(JSONFormatter())
            logger.addHandler(json_handler)
            
            cls._loggers[name] = logger
        
        return cls._loggers[name]

    @classmethod
    def configure_root_logger(cls, level: int = logging.INFO):
        """Configure the root logger with basic settings"""
        logging.basicConfig(
            level=level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[]
        )

# Initialize root logger configuration
AppLogger.configure_root_logger()
