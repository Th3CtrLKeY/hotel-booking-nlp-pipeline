"""
Intent Classification Module

Classifies the primary intent of hotel emails using a hybrid approach:
1. Transformer-based classifier (primary)
2. Rule-based fallback (secondary)

Supported intents:
- booking_request: New booking inquiry
- booking_modification: Change existing booking
- cancellation: Cancel a booking
- price_inquiry: Ask about pricing
- availability_check: Check room availability
- other: Unrelated or unclear
"""

from typing import Dict, Any, Optional
import torch
from transformers import AutoTokenizer, AutoModel
from pathlib import Path


class IntentClassifier:
    """
    Hybrid intent classification using transformers + rules.
    
    Primary method: Fine-tuned transformer encoder
    Fallback: Keyword-based rule matching
    """
    
    def __init__(
        self,
        model_path: Optional[Path] = None,
        use_rule_fallback: bool = True,
        confidence_threshold: float = 0.6
    ):
        """
        Args:
            model_path: Path to trained model (None = use rules only)
            use_rule_fallback: Use rules if ML confidence is low
            confidence_threshold: Minimum confidence for ML prediction
        """
        self.model_path = model_path
        self.use_rule_fallback = use_rule_fallback
        self.confidence_threshold = confidence_threshold
        
        self.model = None
        self.tokenizer = None
        
        # Load model if available
        if model_path and model_path.exists():
            self._load_model(model_path)
    
    def _load_model(self, model_path: Path):
        """Load trained intent classification model."""
        # TODO: Implement in Phase 3
        pass
    
    def classify(self, text: str) -> Dict[str, Any]:
        """
        Classify intent of an email.
        
        Args:
            text: Normalized email text
            
        Returns:
            {
                "intent": str,
                "confidence": float,
                "method": "ml" | "rule" | "default",
                "all_scores": Dict[str, float]
            }
        """
        # Try ML model first
        if self.model is not None:
            ml_result = self._classify_ml(text)
            if ml_result["confidence"] >= self.confidence_threshold:
                ml_result["method"] = "ml"
                return ml_result
        
        # Fallback to rules
        if self.use_rule_fallback:
            rule_result = self._classify_rules(text)
            rule_result["method"] = "rule"
            return rule_result
        
        # Default
        return {
            "intent": "other",
            "confidence": 0.0,
            "method": "default",
            "all_scores": {}
        }
    
    def _classify_ml(self, text: str) -> Dict[str, Any]:
        """ML-based classification."""
        # TODO: Implement in Phase 3
        return {"intent": "other", "confidence": 0.0, "all_scores": {}}
    
    def _classify_rules(self, text: str) -> Dict[str, Any]:
        """Rule-based classification using keyword matching."""
        text_lower = text.lower()
        
        # Keyword patterns
        if any(kw in text_lower for kw in ["book", "reserve", "need a room", "looking for"]):
            return {"intent": "booking_request", "confidence": 0.75, "all_scores": {}}
        elif any(kw in text_lower for kw in ["change", "modify", "update my booking"]):
            return {"intent": "booking_modification", "confidence": 0.75, "all_scores": {}}
        elif any(kw in text_lower for kw in ["cancel", "cancellation"]):
            return {"intent": "cancellation", "confidence": 0.80, "all_scores": {}}
        elif any(kw in text_lower for kw in ["how much", "price", "cost", "rate"]):
            return {"intent": "price_inquiry", "confidence": 0.70, "all_scores": {}}
        elif any(kw in text_lower for kw in ["available", "availability"]):
            return {"intent": "availability_check", "confidence": 0.70, "all_scores": {}}
        else:
            return {"intent": "other", "confidence": 0.5, "all_scores": {}}


def train_intent_classifier(train_data: Path, output_dir: Path):
    """
    Train intent classification model.
    
    Args:
        train_data: Path to training data (JSONL)
        output_dir: Directory to save trained model
    """
    # TODO: Implement in Phase 3
    pass
