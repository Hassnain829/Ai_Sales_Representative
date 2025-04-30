import logging
import random
from transformers import pipeline
from utils.logger import AppLogger

logger = AppLogger.get_logger(__name__)

class ResponseGenerator:
    """Generates context-aware responses using templates and ML"""
    
    def __init__(self):
        self.templates = {
            "pricing": [
                "Our pricing starts at ${price} for basic packages",
                "For your needs, we recommend our ${price} plan"
            ],
            "features": [
                "The {feature} includes {benefits}",
                "You'll get {feature} with these capabilities"
            ]
        }
        self.fallback_model = pipeline("text-generation", model="gpt2")
        
    def generate(self, intent, context=None):
        """
        Generate response based on intent and context
        Args:
            intent: Predicted intent from classifier
            context: Additional conversation context
        Returns:
            dict: {
                "text": generated_response,
                "type": "template|generated",
                "confidence": score
            }
        """
        try:
            if intent in self.templates:
                response = self._use_template(intent, context)
                return {
                    "text": response,
                    "type": "template",
                    "confidence": 1.0
                }
            else:
                return self._generate_response(intent, context)
        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            return {
                "text": "Let me connect you with a specialist.",
                "type": "fallback",
                "confidence": 0
            }
    
    def _use_template(self, intent, context):
        """Select and fill response template"""
        template = random.choice(self.templates[intent])
        # Implement template filling logic
        return template.format(**context)
    
    def _generate_response(self, intent, context):
        """Generate response using language model"""
        prompt = f"Customer asked about {intent}. Context: {context}. Response:"
        result = self.fallback_model(prompt, max_length=50, do_sample=True)
        return {
            "text": result[0]['generated_text'],
            "type": "generated",
            "confidence": 0.7
        }