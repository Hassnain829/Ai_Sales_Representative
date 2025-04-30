from flask import request, jsonify, current_app
from http import HTTPStatus
from typing import Dict, Any
import uuid
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError

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
            # Validate JSON parsing
            try:
                data = request.get_json()
                if data is None:
                    raise ValueError("No JSON data received")
            except Exception as e:
                logger.warning(f"Invalid JSON received: {str(e)}")
                return jsonify({
                    "error": "Invalid JSON format",
                    "details": str(e)
                }), HTTPStatus.BAD_REQUEST
            
            # Validate input
            if not data or 'text' not in data:
                logger.warning("Invalid conversation request received")
                return jsonify({
                    "error": "Missing required 'text' parameter"
                }), HTTPStatus.BAD_REQUEST
            
            # Generate or use existing session ID
            session_id = data.get('session_id', f"conv_{uuid.uuid4().hex[:10]}")
            
            try:
                # Process through sales agent
                result = agent.process_message(data['text'], session_id)
            except Exception as e:
                logger.error(f"Message processing failed: {str(e)}", exc_info=True)
                return jsonify({
                    "error": "Message processing failed",
                    "details": str(e)
                }), HTTPStatus.INTERNAL_SERVER_ERROR
            
            if result['status'] == 'error':
                return jsonify(result), HTTPStatus.INTERNAL_SERVER_ERROR
                
            try:
                # Log successful conversation
                logger.info(f"Processed conversation for session {session_id}")
                return jsonify({
                    "session_id": session_id,
                    "response": result['response'],
                    "analysis": result['analysis']
                })
            except Exception as e:
                logger.error(f"Response formatting failed: {str(e)}")
                return jsonify({
                    "error": "Response formatting error",
                    "details": str(e)
                }), HTTPStatus.INTERNAL_SERVER_ERROR
            
        except Exception as e:
            logger.critical(f"Unexpected error in conversation handler: {str(e)}", exc_info=True)
            return jsonify({
                "error": "Internal server error",
                "details": "An unexpected error occurred"
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
            if not session_id or len(session_id) < 3:  # Basic validation
                return jsonify({
                    "error": "Invalid session ID format"
                }), HTTPStatus.BAD_REQUEST
                
            try:
                conversations = db_manager.get_conversations(session_id=session_id)
            except SQLAlchemyError as e:
                logger.error(f"Database error fetching conversations: {str(e)}")
                return jsonify({
                    "error": "Database error",
                    "details": str(e)
                }), HTTPStatus.INTERNAL_SERVER_ERROR
            except Exception as e:
                logger.error(f"Unexpected error fetching conversations: {str(e)}")
                return jsonify({
                    "error": "Unexpected error",
                    "details": str(e)
                }), HTTPStatus.INTERNAL_SERVER_ERROR
            
            if not conversations:
                logger.info(f"No conversations found for session {session_id}")
                return jsonify({
                    "error": "Conversation not found"
                }), HTTPStatus.NOT_FOUND
                
            try:
                # Format response
                response_data = [{
                    "timestamp": conv.timestamp.isoformat() if conv.timestamp else None,
                    "text": conv.transcript,
                    "response": conv.agent_response,
                    "intent": conv.intent,
                    "sentiment": conv.sentiment
                } for conv in conversations]
                
                return jsonify(response_data)
                
            except Exception as e:
                logger.error(f"Error formatting conversation history: {str(e)}")
                return jsonify({
                    "error": "Error formatting response",
                    "details": str(e)
                }), HTTPStatus.INTERNAL_SERVER_ERROR
                
        except Exception as e:
            logger.critical(f"Critical error in conversation history endpoint: {str(e)}")
            return jsonify({
                "error": "Internal server error",
                "details": "An unexpected error occurred"
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
            # Validate JSON input
            try:
                data = request.get_json()
                if data is None:
                    raise ValueError("No JSON data received")
            except Exception as e:
                logger.warning(f"Invalid JSON in training data: {str(e)}")
                return jsonify({
                    "error": "Invalid JSON format",
                    "details": str(e)
                }), HTTPStatus.BAD_REQUEST
            
            # Validate required fields
            required = ['text', 'intent']
            if not all(field in data for field in required):
                missing = [field for field in required if field not in data]
                logger.warning(f"Missing required fields: {missing}")
                return jsonify({
                    "error": f"Missing required fields: {missing}"
                }), HTTPStatus.BAD_REQUEST
            
            # Validate field contents
            if not isinstance(data['text'], str) or len(data['text'].strip()) < 1:
                return jsonify({
                    "error": "Text must be a non-empty string"
                }), HTTPStatus.BAD_REQUEST
                
            if not isinstance(data['intent'], str) or len(data['intent'].strip()) < 1:
                return jsonify({
                    "error": "Intent must be a non-empty string"
                }), HTTPStatus.BAD_REQUEST
                
            try:
                # Create new training example
                example = TrainingData(
                    text=data['text'].strip(),
                    intent=data['intent'].strip(),
                    entities=data.get('entities', {}),
                    sentiment=data.get('sentiment', 'neutral'),
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
                
            except SQLAlchemyError as e:
                db.session.rollback()
                logger.error(f"Database error adding training data: {str(e)}")
                return jsonify({
                    "error": "Database error",
                    "details": str(e)
                }), HTTPStatus.INTERNAL_SERVER_ERROR
            except Exception as e:
                db.session.rollback()
                logger.error(f"Error adding training data: {str(e)}")
                return jsonify({
                    "error": "Error adding training data",
                    "details": str(e)
                }), HTTPStatus.INTERNAL_SERVER_ERROR
                
        except Exception as e:
            logger.critical(f"Critical error in training data endpoint: {str(e)}")
            return jsonify({
                "error": "Internal server error",
                "details": "An unexpected error occurred"
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
            logger.info("Starting model retraining process")
            
            # Here you would implement:
            # 1. Data collection from database
            # 2. Model training
            # 3. Validation
            # 4. Model deployment
            
            # Simulate a long-running task
            job_id = str(uuid.uuid4())
            logger.info(f"Started retraining job {job_id}")
            
            return jsonify({
                "status": "Retraining initiated",
                "job_id": job_id
            }), HTTPStatus.ACCEPTED
            
        except Exception as e:
            logger.error(f"Model retraining failed: {str(e)}", exc_info=True)
            return jsonify({
                "error": "Retraining failed",
                "details": str(e)
            }), HTTPStatus.INTERNAL_SERVER_ERROR

    @app.route('/health', methods=['GET'])
    def health_check():
        """Simple health check endpoint"""
        try:
            # Check database connection
            try:
                db.session.execute("SELECT 1")
            except SQLAlchemyError as e:
                logger.error(f"Database health check failed: {str(e)}")
                raise Exception(f"Database connection failed: {str(e)}")
            
            # Check ML models
            try:
                agent._check_models()
            except Exception as e:
                logger.error(f"Model health check failed: {str(e)}")
                raise Exception(f"Model check failed: {str(e)}")
            
            return jsonify({
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database": "connected",
                "models": "loaded"
            })
            
        except Exception as e:
            logger.critical(f"Health check failed: {str(e)}", exc_info=True)
            return jsonify({
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }), HTTPStatus.SERVICE_UNAVAILABLE