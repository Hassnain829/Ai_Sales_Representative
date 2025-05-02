from flask import request, jsonify, current_app, render_template, redirect, url_for
from werkzeug.exceptions import NotFound, InternalServerError, BadRequest
from http import HTTPStatus
from typing import Dict, Any
import uuid
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from twilio.base.exceptions import TwilioRestException

from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client
from .models import Conversation, db, TrainingData
from .main import SalesAgent
from .utils.logger import AppLogger
from .utils.db_handler import DatabaseManager
import os

logger = AppLogger.get_logger(__name__)
db_manager = DatabaseManager()
agent = SalesAgent()

def init_routes(app):
    """Initialize all application routes with proper error handling"""
    
    @app.route('/')
    def serve_dashboard():
        """Serve the main dashboard page"""
        try:
            # Verify template exists before rendering
            template_path = os.path.join(app.root_path, 'Templates', 'dashboard.html')
            if not os.path.exists(template_path):
                raise NotFound("dashboard.html not found in templates directory")
                
            return render_template('dashboard.html')
        except NotFound as e:
            logger.error(f"Dashboard template missing: {str(e)}")
            return jsonify({
                "error": "Dashboard unavailable",
                "message": str(e)
            }), HTTPStatus.NOT_FOUND
        except Exception as e:
            logger.error(f"Dashboard rendering failed: {str(e)}")
            return jsonify({
                "error": "Dashboard error",
                "message": str(e)
            }), HTTPStatus.INTERNAL_SERVER_ERROR

    @app.route('/api/v1/conversations', methods=['POST'])
    def handle_conversation():
        """
        Handle customer conversation
        ---
        tags: [Conversations]
        consumes: application/x-www-form-urlencoded
        produces: application/json
        parameters:
          - in: formData
            name: text
            type: string
            required: true
            example: "How much does a website cost?"
          - in: formData
            name: session_id
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
            # Get form data
            text = request.form.get('text')
            session_id = request.form.get('session_id', f"conv_{uuid.uuid4().hex[:10]}")
            
            # Validate input
            if not text:
                logger.warning("Invalid conversation request received")
                return jsonify({
                    "error": "Missing required 'text' parameter"
                }), HTTPStatus.BAD_REQUEST
            
            try:
                # Process through sales agent
                result = agent.process_message(text, session_id)
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
            if not session_id or len(session_id) < 3:
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
        consumes: application/x-www-form-urlencoded
        produces: application/json
        parameters:
          - in: formData
            name: text
            type: string
            required: true
            example: "I need a mobile app"
          - in: formData
            name: intent
            type: string
            required: true
            example: "mobile_development"
          - in: formData
            name: entities
            type: string
            required: false
            example: '{"project_type": "mobile"}'
          - in: formData
            name: sentiment
            type: string
            required: false
            example: "positive"
        responses:
          201:
            description: Training example added
          400:
            description: Invalid input
        """
        try:
            # Get form data
            text = request.form.get('text')
            intent = request.form.get('intent')
            entities_str = request.form.get('entities', '{}')
            sentiment = request.form.get('sentiment', 'neutral')
            
            # Validate required fields
            if not text or not intent:
                missing = [field for field in ['text', 'intent'] if not request.form.get(field)]
                logger.warning(f"Missing required fields: {missing}")
                return jsonify({
                    "error": f"Missing required fields: {missing}"
                }), HTTPStatus.BAD_REQUEST
            
            # Validate field contents
            if not isinstance(text, str) or len(text.strip()) < 1:
                return jsonify({
                    "error": "Text must be a non-empty string"
                }), HTTPStatus.BAD_REQUEST
                
            if not isinstance(intent, str) or len(intent.strip()) < 1:
                return jsonify({
                    "error": "Intent must be a non-empty string"
                }), HTTPStatus.BAD_REQUEST
                
            try:
                # Convert entities string to dict
                entities = {}
                if entities_str:
                    try:
                        entities = eval(entities_str) if isinstance(entities_str, str) else entities_str
                    except:
                        entities = {}
                
                # Create new training example
                example = TrainingData(
                    text=text.strip(),
                    intent=intent.strip(),
                    entities=entities,
                    sentiment=sentiment,
                    source='api',
                    created_at=datetime.utcnow()
                )
                
                db.session.add(example)
                db.session.commit()
                
                logger.info(f"Added training example for intent: {intent}")
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
            db.session.execute("SELECT 1")
            agent._check_models()
            
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
        
    @app.errorhandler(404)
    def handle_not_found(e):
        """Handle 404 errors consistently"""
        if request.path == '/':
            return serve_dashboard()
        return jsonify({
            "error": "Not found",
            "message": f"The requested URL {request.path} was not found"
        }), HTTPStatus.NOT_FOUND  

    @app.route('/voice', methods=['POST'])
    def handle_voice_call():
        """Process incoming voice calls"""
        try:
            resp = VoiceResponse()
            resp.say("Thank you for calling AI Sales Agent. Please wait while we connect you.", 
                     voice='woman')
            return str(resp), 200, {'Content-Type': 'text/xml'}
        except Exception as e:
            logger.error(f"Voice call failed: {str(e)}")
            resp = VoiceResponse()
            resp.say("We're experiencing technical difficulties. Please try again later.")
            return str(resp), 500, {'Content-Type': 'text/xml'}

    @app.route('/config-check')
    def config_check():
        """Check system configuration"""
        try:
            return jsonify({
                'twilio_configured': bool(current_app.config.get('TWILIO_ACCOUNT_SID')),
                'db_configured': bool(current_app.config.get('SQLALCHEMY_DATABASE_URI'))
            })
        except Exception as e:
            logger.error(f"Config check failed: {str(e)}")
            return jsonify({
                "error": "Configuration check failed",
                "details": str(e)
            }), HTTPStatus.INTERNAL_SERVER_ERROR

    @app.route('/initiate_call', methods=['POST'])
    def initiate_call():
        """Handle call initiation from dashboard"""
        try:
            # Get phone number from form data
            phone_number = request.form.get('phone_number')
            
            # Validate input
            if not phone_number:
                return jsonify({
                    "error": "Missing phone number",
                    "message": "Phone number is required"
                }), HTTPStatus.BAD_REQUEST

            # Verify Twilio config
            required_config = ['TWILIO_ACCOUNT_SID', 'TWILIO_AUTH_TOKEN', 'TWILIO_PHONE_NUMBER']
            if not all(current_app.config.get(k) for k in required_config):
                return jsonify({
                    "error": "Twilio configuration missing",
                    "message": "Required Twilio credentials not configured"
                }), HTTPStatus.INTERNAL_SERVER_ERROR

            # Initialize Twilio client
            try:
                client = Client(
                    current_app.config['TWILIO_ACCOUNT_SID'],
                    current_app.config['TWILIO_AUTH_TOKEN']
                )

                # Create call
                call = client.calls.create(
                    to=phone_number,
                    from_=current_app.config['TWILIO_PHONE_NUMBER'],
                    url=url_for('handle_voice_call', _external=True)
                )

                return jsonify({
                    "status": "success",
                    "call_sid": call.sid,
                    "message": "Call initiated successfully"
                }), HTTPStatus.OK

            except TwilioRestException as e:
                logger.error(f"Twilio API error: {str(e)}")
                return jsonify({
                    "error": "Twilio API error",
                    "details": str(e)
                }), HTTPStatus.INTERNAL_SERVER_ERROR
                
        except Exception as e:
            logger.error(f"Call initiation failed: {str(e)}", exc_info=True)
            return jsonify({
                "error": "Internal server error",
                "details": "Failed to initiate call"
            }), HTTPStatus.INTERNAL_SERVER_ERROR

    return app