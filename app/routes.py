from flask import request, jsonify, current_app
from http import HTTPStatus
from typing import Dict, Any
import uuid
from datetime import datetime

from .main import SalesAgent
from .models import db, Conversation, TrainingData
from .utils.logger import AppLogger
from .utils.db_handler import DatabaseManager

logger = AppLogger.get_logger(__name__)
db_manager = DatabaseManager()
agent = SalesAgent()

def init_routes(app):
    """Initialize all application routes with proper error handling"""
    
    @app.route('/api/v1/conversations', methods=['POST'])
    def handle_conversation():
        """
        Handle customer conversation
        ---
        tags: [Conversations]
        consumes: application/json
        produces: application/json
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                text:
                  type: string
                  example: "How much does a website cost?"
                session_id:
                  type: string
                  required: false
                  example: "conv_12345"
        responses:
          200:
            description: Conversation response
          400:
            description: Invalid input
          500:
            description: Internal server error
        """
        try:
            data = request.get_json()
            
            # Validate input
            if not data or 'text' not in data:
                logger.warning("Invalid conversation request received")
                return jsonify({
                    "error": "Missing required 'text' parameter"
                }), HTTPStatus.BAD_REQUEST
            
            # Generate or use existing session ID
            session_id = data.get('session_id', f"conv_{uuid.uuid4().hex[:10]}")
            
            # Process through sales agent
            result = agent.process_message(data['text'], session_id)
            
            if result['status'] == 'error':
                return jsonify(result), HTTPStatus.INTERNAL_SERVER_ERROR
                
            return jsonify({
                "session_id": session_id,
                "response": result['response'],
                "analysis": result['analysis']
            })
            
        except Exception as e:
            logger.error(f"Conversation handler failed: {str(e)}", exc_info=True)
            return jsonify({
                "error": "Internal server error",
                "details": str(e)
            }), HTTPStatus.INTERNAL_SERVER_ERROR

    @app.route('/api/v1/conversations/<session_id>', methods=['GET'])
    def get_conversation_history(session_id: str):
        """
        Retrieve conversation history
        ---
        tags: [Conversations]
        parameters:
          - in: path
            name: session_id
            required: true
            type: string
        responses:
          200:
            description: Conversation history
          404:
            description: Session not found
        """
        try:
            conversations = db_manager.get_conversations(session_id=session_id)
            
            if not conversations:
                return jsonify({
                    "error": "Conversation not found"
                }), HTTPStatus.NOT_FOUND
                
            return jsonify([{
                "timestamp": conv.timestamp.isoformat(),
                "text": conv.transcript,
                "response": conv.agent_response,
                "intent": conv.intent,
                "sentiment": conv.sentiment
            } for conv in conversations])
            
        except Exception as e:
            logger.error(f"Failed to fetch conversation: {str(e)}")
            return jsonify({
                "error": "Internal server error"
            }), HTTPStatus.INTERNAL_SERVER_ERROR

    @app.route('/api/v1/training-data', methods=['POST'])
    def add_training_data():
        """
        Add new training examples
        ---
        tags: [Training]
        consumes: application/json
        produces: application/json
        parameters:
          - in: body
            name: body
            required: true
            schema:
              type: object
              properties:
                text:
                  type: string
                  example: "I need a mobile app"
                intent:
                  type: string
                  example: "mobile_development"
                entities:
                  type: object
                  example: {"project_type": "mobile"}
                sentiment:
                  type: string
                  example: "positive"
        responses:
          201:
            description: Training example added
          400:
            description: Invalid input
        """
        try:
            data = request.get_json()
            
            # Validate required fields
            required = ['text', 'intent']
            if not all(field in data for field in required):
                return jsonify({
                    "error": f"Missing required fields: {required}"
                }), HTTPStatus.BAD_REQUEST
                
            # Create new training example
            example = TrainingData(
                text=data['text'],
                intent=data['intent'],
                entities=data.get('entities'),
                sentiment=data.get('sentiment'),
                source='api',
                created_at=datetime.utcnow()
            )
            
            db.session.add(example)
            db.session.commit()
            
            logger.info(f"Added training example for intent: {data['intent']}")
            return jsonify({
                "status": "success",
                "id": example.id
            }), HTTPStatus.CREATED
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to add training data: {str(e)}")
            return jsonify({
                "error": "Internal server error"
            }), HTTPStatus.INTERNAL_SERVER_ERROR

    @app.route('/api/v1/models/retrain', methods=['POST'])
    def trigger_retraining():
        """
        Trigger model retraining
        ---
        tags: [Training]
        responses:
          202:
            description: Retraining started
          500:
            description: Training failed
        """
        try:
            # In production, this would typically be handled by a task queue
            logger.info("Starting model retraining process")
            
            # Here you would implement:
            # 1. Data collection from database
            # 2. Model training
            # 3. Validation
            # 4. Model deployment
            
            return jsonify({
                "status": "Retraining initiated",
                "job_id": str(uuid.uuid4())
            }), HTTPStatus.ACCEPTED
            
        except Exception as e:
            logger.error(f"Model retraining failed: {str(e)}")
            return jsonify({
                "error": "Retraining failed",
                "details": str(e)
            }), HTTPStatus.INTERNAL_SERVER_ERROR

    @app.route('/health', methods=['GET'])
    def health_check():
        """Simple health check endpoint"""
        try:
            # Check database connection
            db.session.execute("SELECT 1")
            
            # Check ML models
            agent._check_models()
            
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat()
            })
        except Exception as e:
            logger.critical(f"Health check failed: {str(e)}")
            return jsonify({
                "status": "unhealthy",
                "error": str(e)
            }), HTTPStatus.SERVICE_UNAVAILABLE