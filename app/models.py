from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB

db = SQLAlchemy()

class Conversation(db.Model):
    """Stores all customer interactions"""
    __tablename__ = 'conversations'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.String(64), index=True)
    transcript = db.Column(db.Text, nullable=False)
    intent = db.Column(db.String(50))
    entities = db.Column(JSONB)  # Stores extracted entities as JSON
    sentiment = db.Column(db.String(20))
    agent_response = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    outcome = db.Column(db.String(50))  # conversion, lost, follow_up
    duration = db.Column(db.Float)     # Call duration in seconds
    needs_review = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Conversation {self.session_id}>'

class TrainingData(db.Model):
    """Stores labeled training examples"""
    __tablename__ = 'training_data'
    
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    intent = db.Column(db.String(50), nullable=False)
    entities = db.Column(JSONB)
    sentiment = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(50))  # manual, auto_labeled, imported

    def to_dict(self):
        return {
            'text': self.text,
            'intent': self.intent,
            'entities': self.entities,
            'sentiment': self.sentiment
        }