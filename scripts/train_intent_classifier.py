"""
Training script for intent classification model.

Trains a transformer-based intent classifier on the prepared dataset.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.intent import IntentClassifier
import yaml
import json
import matplotlib.pyplot as plt


def plot_training_history(history: dict, output_path: Path):
    """Plot training history."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
    
    # Loss plot
    ax1.plot(history['train_loss'], label='Train Loss')
    if 'val_loss' in history and history['val_loss']:
        ax1.plot(history['val_loss'], label='Val Loss')
    ax1.set_xlabel('Epoch')
    ax1.set_ylabel('Loss')
    ax1.set_title('Training Loss')
    ax1.legend()
    ax1.grid(True)
    
    # Accuracy plot
    ax2.plot(history['train_acc'], label='Train Acc')
    if 'val_acc' in history and history['val_acc']:
        ax2.plot(history['val_acc'], label='Val Acc')
    ax2.set_xlabel('Epoch')
    ax2.set_ylabel('Accuracy (%)')
    ax2.set_title('Training Accuracy')
    ax2.legend()
    ax2.grid(True)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nSaved training history plot to: {output_path}")


def main():
    """Main training function."""
    # Paths
    project_root = Path(__file__).parent.parent
    config_path = project_root / "config" / "intent_model.yaml"
    train_data = project_root / "data" / "processed" / "intent_train.jsonl"
    test_data = project_root / "data" / "processed" / "intent_test.jsonl"
    output_dir = project_root / "models" / "intent_classifier"
    results_dir = project_root / "results"
    results_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Intent Classifier Training")
    print("=" * 60)
    
    # Check data exists
    if not train_data.exists():
        print(f"\nError: Training data not found at {train_data}")
        print("Please run: python scripts/prepare_intent_data.py")
        return
    
    # Load config
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print(f"\nConfiguration:")
    print(f"  Base model: {config['model']['base_model']}")
    print(f"  Epochs: {config['training']['epochs']}")
    print(f"  Batch size: {config['training']['batch_size']}")
    print(f"  Learning rate: {config['training']['learning_rate']}")
    
    # Initialize classifier
    classifier = IntentClassifier(config_path=config_path)
    
    # Train
    print(f"\nTraining data: {train_data}")
    print(f"Test data: {test_data}")
    print(f"Output: {output_dir}\n")
    
    history = classifier.train_model(
        train_data_path=train_data,
        val_data_path=test_data,
        output_dir=output_dir
    )
    
    # Save history
    history_path = results_dir / "intent_training_history.json"
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
    print(f"\nSaved training history to: {history_path}")
    
    # Plot history
    plot_path = results_dir / "intent_training_history.png"
    plot_training_history(history, plot_path)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    print(f"Final Training Accuracy: {history['train_acc'][-1]:.2f}%")
    if 'val_acc' in history and history['val_acc']:
        print(f"Final Validation Accuracy: {history['val_acc'][-1]:.2f}%")
    print(f"\nModel saved to: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
