"""
Data preparation script for intent classification.

Extracts intent labels from ground truth and creates train/test split.
"""

import json
import yaml
from pathlib import Path
from typing import List, Dict, Tuple
import random


def load_ground_truth(labels_path: Path) -> List[Dict]:
    """Load ground truth labels from JSONL file."""
    labels = []
    with open(labels_path, 'r') as f:
        for line in f:
            labels.append(json.loads(line))
    return labels


def load_email_text(email_id: str, emails_dir: Path) -> str:
    """Load raw email text for a given email ID."""
    # Convert email_id to filename (e.g., "email_001" -> "email_001.txt")
    if not email_id.endswith('.txt'):
        email_file = emails_dir / f"{email_id}.txt"
    else:
        email_file = emails_dir / email_id
    
    with open(email_file, 'r', encoding='utf-8') as f:
        return f.read()


def prepare_intent_dataset(
    labels_path: Path,
    emails_dir: Path,
    config: Dict
) -> Tuple[List[Dict], List[Dict]]:
    """
    Prepare intent classification dataset.
    
    Returns:
        (train_data, test_data) - Lists of {"text": str, "intent": str}
    """
    # Load ground truth
    ground_truth = load_ground_truth(labels_path)
    
    # Extract intent data
    dataset = []
    for entry in ground_truth:
        email_id = entry['email_id']
        intent = entry['intent']
        
        try:
            text = load_email_text(email_id, emails_dir)
            dataset.append({
                "email_id": email_id,
                "text": text,
                "intent": intent
            })
        except FileNotFoundError:
            print(f"Warning: Email file not found for {email_id}, skipping")
            continue
    
    # Stratified split by intent
    random.seed(config['data']['random_seed'])
    
    # Group by intent
    intent_groups = {}
    for item in dataset:
        intent = item['intent']
        if intent not in intent_groups:
            intent_groups[intent] = []
        intent_groups[intent].append(item)
    
    # Split each intent group
    train_data = []
    test_data = []
    train_split = config['data']['train_split']
    
    for intent, items in intent_groups.items():
        random.shuffle(items)
        split_idx = int(len(items) * train_split)
        train_data.extend(items[:split_idx])
        test_data.extend(items[split_idx:])
    
    # Shuffle combined datasets
    random.shuffle(train_data)
    random.shuffle(test_data)
    
    return train_data, test_data


def save_dataset(data: List[Dict], output_path: Path):
    """Save dataset to JSONL format."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in data:
            # Save only text and intent (not email_id)
            json.dump({
                "text": item['text'],
                "intent": item['intent']
            }, f)
            f.write('\n')


def print_dataset_stats(train_data: List[Dict], test_data: List[Dict]):
    """Print dataset statistics."""
    print("\n" + "=" * 60)
    print("Intent Classification Dataset Statistics")
    print("=" * 60)
    
    # Count intents
    def count_intents(data):
        counts = {}
        for item in data:
            intent = item['intent']
            counts[intent] = counts.get(intent, 0) + 1
        return counts
    
    train_counts = count_intents(train_data)
    test_counts = count_intents(test_data)
    
    print(f"\nTotal emails: {len(train_data) + len(test_data)}")
    print(f"Training: {len(train_data)} emails")
    print(f"Test: {len(test_data)} emails")
    
    print("\nIntent distribution:")
    print(f"{'Intent':<25} {'Train':<10} {'Test':<10} {'Total':<10}")
    print("-" * 60)
    
    all_intents = set(train_counts.keys()) | set(test_counts.keys())
    for intent in sorted(all_intents):
        train_count = train_counts.get(intent, 0)
        test_count = test_counts.get(intent, 0)
        total = train_count + test_count
        print(f"{intent:<25} {train_count:<10} {test_count:<10} {total:<10}")
    
    print("=" * 60 + "\n")


def main():
    """Main execution function."""
    # Paths
    project_root = Path(__file__).parent.parent
    labels_path = project_root / "data" / "labels" / "ground_truth.jsonl"
    emails_dir = project_root / "data" / "raw_emails"
    config_path = project_root / "config" / "intent_model.yaml"
    
    output_dir = project_root / "data" / "processed"
    train_output = output_dir / "intent_train.jsonl"
    test_output = output_dir / "intent_test.jsonl"
    
    # Load configuration
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    print("Preparing intent classification dataset...")
    print(f"Ground truth: {labels_path}")
    print(f"Emails directory: {emails_dir}")
    
    # Prepare dataset
    train_data, test_data = prepare_intent_dataset(
        labels_path, emails_dir, config
    )
    
    # Save datasets
    save_dataset(train_data, train_output)
    save_dataset(test_data, test_output)
    
    print(f"\nSaved training data to: {train_output}")
    print(f"Saved test data to: {test_output}")
    
    # Print statistics
    print_dataset_stats(train_data, test_data)


if __name__ == "__main__":
    main()
