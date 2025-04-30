import logging
from datetime import datetime
from textblob import TextBlob
import torch
from transformers import pipeline
from .models import db, Conversation
from .utils.logger import AppLogger
from .utils.db_handler import DatabaseManager
from .utils.config import Config

logger = AppLogger.get_logger(__name__)

class SalesAgent:
    """Main AI sales agent class"""
    
    def __init__(self):
        self.intent_classifier = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device="cuda" if torch.cuda.is_available() else "cpu"
        )
        self.sentiment_analyzer = pipeline(
            "text-classification",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
        self.db = DatabaseManager()
        
    def process_message(self, text, session_id):
        """
        Process customer message and generate response
        Args:
            text: Customer input text
            session_id: Unique conversation ID
        Returns:
            dict: Generated response and metadata
        """
        try:
            # Step 1: Analyze customer input
            analysis = self._analyze_text(text)
            
            # Step 2: Generate appropriate response
            response = self._generate_response(analysis)
            
            # Step 3: Log interaction
            self._log_interaction(
                session_id=session_id,
                text=text,
                analysis=analysis,
                response=response['text']
            )
            
            return {
                'status': 'success',
                'response': response,
                'analysis': analysis
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': str(e)
            }

    def _analyze_text(self, text):
        """Perform NLP analysis on input text"""
        # Intent classification
        intent_result = self.intent_classifier(
            text,
            candidate_labels=["sales", "support", "billing", "technical"]
        )
        
        # Sentiment analysis
        sentiment_result = self.sentiment_analyzer(text)[0]
        
        # Entity extraction
        entities = self._extract_entities(text)
        
        return {
            'text': text,
            'intent': intent_result['labels'][0],
            'intent_confidence': float(intent_result['scores'][0]),
            'sentiment': sentiment_result['label'],
            'sentiment_score': float(sentiment_result['score']),
            'entities': entities,
            'timestamp': datetime.utcnow()
        }

    def _extract_entities(self, text):
        """Extract key entities from text"""
        # Implement your entity extraction logic
        return {
            'product': self._extract_product(text),
            'budget': self._extract_budget(text),
            'timeline': self._extract_timeline(text)
        }

    def _generate_response(self, analysis):
        """Generate context-aware response"""
        # Implement your response generation logic
        if analysis['intent'] == 'sales':
            return self._handle_sales_intent(analysis)
        elif analysis['intent'] == 'support':
            return self._handle_support_intent(analysis)
        else:
            return self._handle_fallback(analysis)

    def _log_interaction(self, session_id, text, analysis, response):
        """Save conversation to database"""
        try:
            conversation = Conversation(
                session_id=session_id,
                transcript=text,
                intent=analysis['intent'],
                entities=analysis['entities'],
                sentiment=analysis['sentiment'],
                agent_response=response,
                timestamp=analysis['timestamp']
            )
            self.db.session.add(conversation)
            self.db.session.commit()
            logger.info(f"Logged conversation: {session_id}")
        except Exception as e:
            logger.error(f"Failed to log conversation: {str(e)}")
            self.db.session.rollback()