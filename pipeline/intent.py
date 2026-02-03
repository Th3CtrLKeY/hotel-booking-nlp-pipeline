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

from typing import Dict, Any, Optional, List
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer, AutoModel
from pathlib import Path
import json
import yaml
from tqdm import tqdm
import numpy as np


class IntentDataset(Dataset):
    """Dataset for intent classification."""
    
    def __init__(self, data_path: Path, tokenizer, max_length: int = 128):
        self.data = []
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                self.data.append(json.loads(line))
        
        self.tokenizer = tokenizer
        self.max_length = max_length
        
        #  Create intent to index mapping
        self.intent_to_idx = {
            "booking_request": 0,
            "booking_modification": 1,
            "cancellation": 2,
            "price_inquiry": 3,
            "availability_check": 4,
            "other": 5
        }
        self.idx_to_intent = {v: k for k, v in self.intent_to_idx.items()}
    
    def __len__(self):
        return len(self.data)
    
    def __getitem__(self, idx):
        item = self.data[idx]
        text = item['text']
        intent = item['intent']
        
        # Tokenize
        encoding = self.tokenizer(
            text,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].squeeze(0),
            'attention_mask': encoding['attention_mask'].squeeze(0),
            'label': torch.tensor(self.intent_to_idx[intent], dtype=torch.long)
        }


class IntentClassifierModel(nn.Module):
    """Transformer-based intent classification model."""
    
    def __init__(self, base_model: str, num_classes: int, dropout: float = 0.1):
        super().__init__()
        self.encoder = AutoModel.from_pretrained(base_model)
        self.dropout = nn.Dropout(dropout)
        self.classifier = nn.Linear(self.encoder.config.hidden_size, num_classes)
    
    def forward(self, input_ids, attention_mask):
        # Get [CLS] token embedding
        outputs = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.last_hidden_state[:, 0, :]  # [CLS] token
        
        pooled_output = self.dropout(pooled_output)
        logits = self.classifier(pooled_output)
        
        return logits


class IntentClassifier:
    """
    Hybrid intent classification using transformers + rules.
    
    Primary method: Fine-tuned transformer encoder
    Fallback: Keyword-based rule matching
    """
    
    def __init__(
        self,
        model_path: Optional[Path] = None,
        config_path: Optional[Path] = None,
        use_rule_fallback: bool = True,
        confidence_threshold: float = 0.6
    ):
        """
        Args:
            model_path: Path to trained model (None = use rules only)
            config_path: Path to intent_model.yaml
            use_rule_fallback: Use rules if ML confidence is low
            confidence_threshold: Minimum confidence for ML prediction
        """
        self.model_path = model_path
        self.use_rule_fallback = use_rule_fallback
        self.confidence_threshold = confidence_threshold
        
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "intent_model.yaml"
        
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        self.model = None
        self.tokenizer = None
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Intent mappings
        self.intent_to_idx = {
            "booking_request": 0,
            "booking_modification": 1,
            "cancellation": 2,
            "price_inquiry": 3,
            "availability_check": 4,
            "other": 5
        }
        self.idx_to_intent = {v: k for k, v in self.intent_to_idx.items()}
        
        # Load model if available
        if model_path and model_path.exists():
            self.load(model_path)
    
    def load(self, model_path: Path):
        """Load trained model."""
        print(f"Loading model from {model_path}")
        
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # Load model
        self.model = IntentClassifierModel(
            base_model=self.config['model']['base_model'],
            num_classes=self.config['model']['num_classes'],
            dropout=self.config['model']['hidden_dropout']
        )
        
        # Load weights
        state_dict = torch.load(model_path / "model.pt", map_location=self.device)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()
    
    def save(self, output_dir: Path):
        """Save trained model."""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Save model weights
        torch.save(self.model.state_dict(), output_dir / "model.pt")
        
        # Save tokenizer
        self.tokenizer.save_pretrained(output_dir)
        
        # Save config
        with open(output_dir / "config.yaml", 'w') as f:
            yaml.dump(self.config, f)
        
        print(f"Model saved to {output_dir}")
    
    def train_model(
        self,
        train_data_path: Path,
        val_data_path: Optional[Path] = None,
        output_dir: Optional[Path] = None
    ) -> Dict[str, List[float]]:
        """
        Train the intent classification model.
        
        Args:
            train_data_path: Path to training data (JSONL)
            val_data_path: Path to validation data (JSONL)
            output_dir: Directory to save model
            
        Returns:
            Training history (loss, accuracy per epoch)
        """
        # Initialize tokenizer and model
        base_model = self.config['model']['base_model']
        self.tokenizer = AutoTokenizer.from_pretrained(base_model)
        
        self.model = IntentClassifierModel(
            base_model=base_model,
            num_classes=self.config['model']['num_classes'],
            dropout=self.config['model']['hidden_dropout']
        )
        self.model.to(self.device)
        
        # Create datasets
        train_dataset = IntentDataset(train_data_path, self.tokenizer)
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.config['training']['batch_size'],
            shuffle=True
        )
        
        if val_data_path:
            val_dataset = IntentDataset(val_data_path, self.tokenizer)
            val_loader = DataLoader(
                val_dataset,
                batch_size=self.config['training']['batch_size']
            )
        
        # Training setup
        optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=float(self.config['training']['learning_rate']),
            weight_decay=float(self.config['training']['weight_decay'])
        )
        
        criterion = nn.CrossEntropyLoss()
        
        # Training loop
        epochs = self.config['training']['epochs']
        history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}
        
        print(f"\nTraining on {self.device}")
        print(f"Epochs: {epochs}, Batch size: {self.config['training']['batch_size']}")
        print(f"Training samples: {len(train_dataset)}")
        if val_data_path:
            print(f"Validation samples: {len(val_dataset)}\n")
        
        for epoch in range(epochs):
            # Training
            self.model.train()
            train_loss = 0
            train_correct = 0
            train_total = 0
            
            pbar = tqdm(train_loader, desc=f"Epoch {epoch+1}/{epochs}")
            for batch in pbar:
                input_ids = batch['input_ids'].to(self.device)
                attention_mask = batch['attention_mask'].to(self.device)
                labels = batch['label'].to(self.device)
                
                optimizer.zero_grad()
                
                logits = self.model(input_ids, attention_mask)
                loss = criterion(logits, labels)
                
                loss.backward()
                torch.nn.utils.clip_grad_norm_(
                    self.model.parameters(),
                    self.config['training']['max_grad_norm']
                )
                optimizer.step()
                
                train_loss += loss.item()
                _, predicted = torch.max(logits, 1)
                train_correct += (predicted == labels).sum().item()
                train_total += labels.size(0)
                
                pbar.set_postfix({
                    'loss': f"{loss.item():.4f}",
                    'acc': f"{100 * train_correct / train_total:.2f}%"
                })
            
            avg_train_loss = train_loss / len(train_loader)
            train_acc = 100 * train_correct / train_total
            
            history['train_loss'].append(avg_train_loss)
            history['train_acc'].append(train_acc)
            
            # Validation
            if val_data_path:
                self.model.eval()
                val_loss = 0
                val_correct = 0
                val_total = 0
                
                with torch.no_grad():
                    for batch in val_loader:
                        input_ids = batch['input_ids'].to(self.device)
                        attention_mask = batch['attention_mask'].to(self.device)
                        labels = batch['label'].to(self.device)
                        
                        logits = self.model(input_ids, attention_mask)
                        loss = criterion(logits, labels)
                        
                        val_loss += loss.item()
                        _, predicted = torch.max(logits, 1)
                        val_correct += (predicted == labels).sum().item()
                        val_total += labels.size(0)
                
                avg_val_loss = val_loss / len(val_loader)
                val_acc = 100 * val_correct / val_total
                
                history['val_loss'].append(avg_val_loss)
                history['val_acc'].append(val_acc)
                
                print(f"Epoch {epoch+1}: Train Loss={avg_train_loss:.4f}, Train Acc={train_acc:.2f}%, "
                      f"Val Loss={avg_val_loss:.4f}, Val Acc={val_acc:.2f}%")
            else:
                print(f"Epoch {epoch+1}: Train Loss={avg_train_loss:.4f}, Train Acc={train_acc:.2f}%")
        
        # Save model
        if output_dir:
            self.save(output_dir)
        
        return history
    
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
        if self.model is None or self.tokenizer is None:
            return {"intent": "other", "confidence": 0.0, "all_scores": {}}
        
        self.model.eval()
        
        # Tokenize
        encoding = self.tokenizer(
            text,
            max_length=128,
            padding='max_length',
            truncation=True,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        # Predict
        with torch.no_grad():
            logits = self.model(input_ids, attention_mask)
            probs = torch.softmax(logits, dim=1)[0]
        
        # Get prediction
        confidence, pred_idx = torch.max(probs, 0)
        intent = self.idx_to_intent[pred_idx.item()]
        
        # All scores
        all_scores = {
            self.idx_to_intent[i]: probs[i].item()
            for i in range(len(probs))
        }
        
        return {
            "intent": intent,
            "confidence": confidence.item(),
            "all_scores": all_scores
        }
    
    def _classify_rules(self, text: str) -> Dict[str, Any]:
        """Rule-based classification using keyword matching."""
        text_lower = text.lower()
        
        # Keyword patterns with confidence scores
        if any(kw in text_lower for kw in ["book", "reserve", "need a room", "looking for", "i need", "we need"]):
            return {"intent": "booking_request", "confidence": 0.75, "all_scores": {}}
        elif any(kw in text_lower for kw in ["change", "modify", "update my booking", "update my reservation"]):
            return {"intent": "booking_modification", "confidence": 0.75, "all_scores": {}}
        elif any(kw in text_lower for kw in ["cancel", "cancellation"]):
            return {"intent": "cancellation", "confidence": 0.80, "all_scores": {}}
        elif any(kw in text_lower for kw in ["how much", "price", "cost", "rate", "quote"]):
            return {"intent": "price_inquiry", "confidence": 0.70, "all_scores": {}}
        elif any(kw in text_lower for kw in ["available", "availability", "do you have"]):
            return {"intent": "availability_check", "confidence": 0.70, "all_scores": {}}
        else:
            return {"intent": "other", "confidence": 0.5, "all_scores": {}}
