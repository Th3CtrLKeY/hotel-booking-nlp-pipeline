"""
Split ground truth dataset into train/test sets with stratified sampling.

Creates:
- data/processed/ground_truth_train.jsonl (80%)
- data/processed/ground_truth_test.jsonl (20%)
- data/processed/intent_train.jsonl (intent only, for classifier)
- data/processed/intent_test.jsonl (intent only, for classifier)
"""

import json
import random
from pathlib import Path
from collections import Counter

# Set random seed for reproducibility
random.seed(42)


def load_data(file_path):
    """Load JSONL data."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return [json.loads(line) for line in f]


def stratified_split(data, test_size=0.2):
    """
    Split data into train/test sets with stratified sampling by intent.
    
    Args:
        data: List of email dictionaries
        test_size: Fraction of data for test set (default: 0.2)
    
    Returns:
        train_data, test_data
    """
    # Group by intent
    intent_groups = {}
    for item in data:
        intent = item['intent']
        if intent not in intent_groups:
            intent_groups[intent] = []
        intent_groups[intent].append(item)
    
    train_data = []
    test_data = []
    
    # Split each group
    for intent, items in intent_groups.items():
        # Shuffle within intent group
        shuffled = items.copy()
        random.shuffle(shuffled)
        
        # Calculate split point
        n_test = max(1, int(len(shuffled) * test_size))  # At least 1 test sample per intent
        
        # Split
        test_data.extend(shuffled[:n_test])
        train_data.extend(shuffled[n_test:])
    
    # Final shuffle
    random.shuffle(train_data)
    random.shuffle(test_data)
    
    return train_data, test_data


def save_jsonl(data, file_path):
    """Save data to JSONL file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        for item in data:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')


def create_intent_only(data):
    """Extract only text and intent for intent classifier."""
    return [
        {
            'text': item['raw_email'],
            'intent': item['intent']
        }
        for item in data
    ]


def print_distribution(data, label):
    """Print intent distribution."""
    intents = Counter(item['intent'] for item in data)
    total = len(data)
    
    print(f"\n{label}:")
    print(f"  Total: {total}")
    for intent, count in sorted(intents.items()):
        pct = 100 * count / total
        print(f"    {intent:<25} {count:>3} ({pct:>5.1f}%)")


def main():
    print("=" * 60)
    print("Ground Truth Data Splitting")
    print("=" * 60)
    
    # Paths
    base_dir = Path(__file__).parent.parent
    source_file = base_dir / "data" / "labels" / "ground_truth.jsonl"
    
    # Output paths
    train_full = base_dir / "data" / "processed" / "ground_truth_train.jsonl"
    test_full = base_dir / "data" / "processed" / "ground_truth_test.jsonl"
    train_intent = base_dir / "data" / "processed" / "intent_train.jsonl"
    test_intent = base_dir / "data" / "processed" / "intent_test.jsonl"
    
    # Load data
    print(f"\nLoading data from: {source_file}")
    data = load_data(source_file)
    print(f"[OK] Loaded {len(data)} emails")
    
    # Show original distribution
    print_distribution(data, "Original Data")
    
    # Split
    print("\n" + "-" * 60)
    print("Performing Stratified Split (80/20)")
    print("-" * 60)
    
    train_data, test_data = stratified_split(data, test_size=0.2)
    
    # Show split distributions
    print_distribution(train_data, "Training Set")
    print_distribution(test_data, "Test Set")
    
    # Save full ground truth files
    print("\n" + "-" * 60)
    print("Saving Files")
    print("-" * 60)
    
    save_jsonl(train_data, train_full)
    print(f"[OK] Saved: {train_full}")
    
    save_jsonl(test_data, test_full)
    print(f"[OK] Saved: {test_full}")
    
    # Create and save intent-only files
    train_intent_data = create_intent_only(train_data)
    test_intent_data = create_intent_only(test_data)
    
    save_jsonl(train_intent_data, train_intent)
    print(f"[OK] Saved: {train_intent}")
    
    save_jsonl(test_intent_data, test_intent)
    print(f"[OK] Saved: {test_intent}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Training samples: {len(train_data)} ({100 * len(train_data) / len(data):.1f}%)")
    print(f"Test samples: {len(test_data)} ({100 * len(test_data) / len(data):.1f}%)")
    print(f"\nFiles created:")
    print(f"  - {train_full.relative_to(base_dir)}")
    print(f"  - {test_full.relative_to(base_dir)}")
    print(f"  - {train_intent.relative_to(base_dir)}")
    print(f"  - {test_intent.relative_to(base_dir)}")
    print("=" * 60)


if __name__ == "__main__":
   main()
