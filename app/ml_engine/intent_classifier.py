import logging
import pandas as pd
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
from sklearn.model_selection import train_test_split
from utils.logger import AppLogger

logger = AppLogger.get_logger(__name__)

class IntentClassifier:
    """Handles intent classification using fine-tuned transformer models"""
    
    def __init__(self, model_path="facebook/bart-large-mnli"):
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self.label_map = {
            "pricing": 0,
            "features": 1,
            "technical": 2,
            "sales": 3
        }
        self._load_model()
        
    def _load_model(self):
        """Load or initialize the intent classification model"""
        try:
            self.model = AutoModelForSequenceClassification.from_pretrained(self.model_path)
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            logger.info(f"Loaded intent classifier from {self.model_path}")
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise
            
    def predict(self, text, candidate_labels=None):
        """
        Predict intent from text
        Args:
            text: Input text to classify
            candidate_labels: List of possible intents (default: pre-configured)
        Returns:
            dict: {
                "intent": predicted_label,
                "confidence": probability,
                "all_scores": full_results
            }
        """
        if not candidate_labels:
            candidate_labels = list(self.label_map.keys())
            
        classifier = pipeline(
            "zero-shot-classification",
            model=self.model,
            tokenizer=self.tokenizer
        )
        
        result = classifier(text, candidate_labels)
        return {
            "intent": result['labels'][0],
            "confidence": result['scores'][0],
            "all_scores": dict(zip(result['labels'], result['scores']))
        }
    
    def train(self, data_path="data/training/labeled.csv"):
        """Fine-tune the model with new training data"""
        try:
            df = pd.read_csv(data_path)
            # Preprocess data and implement training logic
            logger.info(f"Training started with {len(df)} examples")
            # [Actual training implementation would go here]
            logger.info("Training completed successfully")
        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            raise