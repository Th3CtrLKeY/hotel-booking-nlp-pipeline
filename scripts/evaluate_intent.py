"""
Evaluation script for intent classification model.

Generates comprehensive evaluation metrics including:
- Classification report (precision, recall, F1)
- Confusion matrix
- Per-class performance
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.intent import IntentClassifier
import json
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import matplotlib.pyplot as plt
import seaborn as sns


def load_test_data(test_data_path: Path):
    """Load test data and return texts and labels."""
    texts = []
    labels = []
    
    with open(test_data_path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            texts.append(item['text'])
            labels.append(item['intent'])
    
    return texts, labels


def evaluate_model(classifier: IntentClassifier, texts: list, true_labels: list):
    """Evaluate model and return predictions."""
    predictions = []
    confidences = []
    methods = []
    
    for text in texts:
        result = classifier.classify(text)
        predictions.append(result['intent'])
        confidences.append(result['confidence'])
        methods.append(result['method'])
    
    return predictions, confidences, methods


def plot_confusion_matrix(y_true, y_pred, labels, output_path: Path):
    """Plot confusion matrix."""
    cm = confusion_matrix(y_true, y_pred, labels=labels)
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(
        cm,
        annot=True,
        fmt='d',
        cmap='Blues',
        xticklabels=labels,
        yticklabels=labels,
        cbar_kws={'label': 'Count'}
    )
    plt.xlabel('Predicted Intent')
    plt.ylabel('True Intent')
    plt.title('Intent Classification Confusion Matrix')
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved confusion matrix to: {output_path}")


def main():
    """Main evaluation function."""
    # Paths
    project_root = Path(__file__).parent.parent
    model_dir = project_root / "models" / "intent_classifier"
    test_data = project_root / "data" / "processed" / "intent_test.jsonl"
    results_dir = project_root / "results"
    results_dir.mkdir(exist_ok=True)
    
    print("=" * 60)
    print("Intent Classifier Evaluation")
    print("=" * 60)
    
    # Check model exists
    if not model_dir.exists():
        print(f"\nError: Model not found at {model_dir}")
        print("Please train the model first: python scripts/train_intent_classifier.py")
        return
    
    # Load model
    print(f"\nLoading model from: {model_dir}")
    classifier = IntentClassifier(model_path=model_dir)
    
    # Load test data
    print(f"Loading test data from: {test_data}")
    texts, true_labels = load_test_data(test_data)
    print(f"Test samples: {len(texts)}\n")
    
    # Evaluate
    print("Running evaluation...")
    predictions, confidences, methods = evaluate_model(classifier, texts, true_labels)
    
    # Calculate metrics
    accuracy = accuracy_score(true_labels, predictions)
    
    # All possible intents
    all_intents = [
        "booking_request",
        "booking_modification",
        "cancellation",
        "price_inquiry",
        "availability_check",
        "other"
    ]
    
    # Classification report
    report = classification_report(
        true_labels,
        predictions,
        labels=all_intents,
        zero_division=0,
        output_dict=True
    )
    
    # Print results
    print("\n" + "=" * 60)
    print("Evaluation Results")
    print("=" * 60)
    print(f"\nOverall Accuracy: {accuracy * 100:.2f}%\n")
    
    print("Per-Intent Performance:")
    print(f"{'Intent':<25} {'Precision':<12} {'Recall':<12} {'F1-Score':<12} {'Support':<10}")
    print("-" * 80)
    
    for intent in all_intents:
        if intent in report:
            metrics = report[intent]
            print(f"{intent:<25} {metrics['precision']:<12.3f} {metrics['recall']:<12.3f} "
                  f"{metrics['f1-score']:<12.3f} {int(metrics['support']):<10}")
    
    print("-" * 80)
    print(f"{'Macro Avg':<25} {report['macro avg']['precision']:<12.3f} "
          f"{report['macro avg']['recall']:<12.3f} {report['macro avg']['f1-score']:<12.3f}")
    print(f"{'Weighted Avg':<25} {report['weighted avg']['precision']:<12.3f} "
          f"{report['weighted avg']['recall']:<12.3f} {report['weighted avg']['f1-score']:<12.3f}")
    
    # Method distribution
    ml_count = methods.count('ml')
    rule_count = methods.count('rule')
    print(f"\nClassification Methods:")
    print(f"  ML-based: {ml_count}/{len(methods)} ({100*ml_count/len(methods):.1f}%)")
    print(f"  Rule-based: {rule_count}/{len(methods)} ({100*rule_count/len(methods):.1f}%)")
    
    # Average confidence
    avg_confidence = np.mean(confidences)
    print(f"\nAverage Confidence: {avg_confidence:.3f}")
    
    # Save results
    metrics_path = results_dir / "intent_evaluation.json"
    with open(metrics_path, 'w') as f:
        json.dump({
            "accuracy": accuracy,
            "classification_report": report,
            "method_distribution": {
                "ml": ml_count,
                "rule": rule_count
            },
            "average_confidence": avg_confidence
        }, f, indent=2)
    print(f"\nSaved metrics to: {metrics_path}")
    
    # Save detailed classification report
    report_path = results_dir / "classification_report.txt"
    with open(report_path, 'w') as f:
        f.write("Intent Classification Report\n")
        f.write("=" * 60 + "\n\n")
        f.write(classification_report(
            true_labels,
            predictions,
            labels=all_intents,
            zero_division=0
        ))
    print(f"Saved classification report to: {report_path}")
    
    # Plot confusion matrix
    cm_path = results_dir / "confusion_matrix.png"
    plot_confusion_matrix(true_labels, predictions, all_intents, cm_path)
    
    # Print individual predictions
    print("\n" + "=" * 60)
    print("Individual Predictions")
    print("=" * 60)
    for i, (text, true, pred, conf, method) in enumerate(zip(texts, true_labels, predictions, confidences, methods)):
        status = "[OK]" if true == pred else "[FAIL]"
        print(f"\n{status} Sample {i+1}:")
        print(f"  True: {true}")
        print(f"  Predicted: {pred} (confidence: {conf:.3f}, method: {method})")
        print(f"  Text preview: {text[:100]}...")
    
    print("\n" + "=" * 60)
    print("Evaluation Complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
