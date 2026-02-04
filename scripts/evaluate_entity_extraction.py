"""
Evaluate entity extraction on ground truth test set.

Compares extracted entities against annotated ground truth for:
- Date accuracy (arrival, departure, nights)
- Guest count accuracy (adults, children with ages)
- Room type accuracy
- Multi-segment detection

Generates detailed error analysis and metrics.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Any

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.entities import EntityExtractor


def load_test_data(file_path: Path) -> List[Dict]:
    """Load test set from JSONL."""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            data.append(json.loads(line))
    return data


def evaluate_dates(predicted: Dict, expected: Dict) -> Dict[str, bool]:
    """
    Evaluate date extraction accuracy.
    
    Returns: {
        "arrival_correct": bool,
        "departure_correct": bool,
        "nights_correct": bool
    }
    """
    return {
        "arrival_correct": predicted.get("arrival_date") == expected.get("arrival_date"),
        "departure_correct": predicted.get("departure_date") == expected.get("departure_date"),
        "nights_correct": predicted.get("nights") == expected.get("nights")
    }


def evaluate_guests(predicted: Dict, expected: Dict) -> Dict[str, Any]:
    """
    Evaluate guest count accuracy.
    
    Returns: {
        "adults_correct": bool,
        "children_count_correct": bool,
        "children_ages_correct": bool
    }
    """
    adults_correct = predicted.get("adults") == expected.get("adults")
    
    pred_children = predicted.get("children", [])
    exp_children = expected.get("children", [])
    
    children_count_correct = len(pred_children) == len(exp_children)
    
    # Check if ages match (order doesn't matter)
    pred_ages = sorted([c.get("age") for c in pred_children if c.get("age") is not None])
    exp_ages = sorted([c.get("age") for c in exp_children if c.get("age") is not None])
    children_ages_correct = pred_ages == exp_ages
    
    return {
        "adults_correct": adults_correct,
        "children_count_correct": children_count_correct,
        "children_ages_correct": children_ages_correct
    }


def evaluate_room_types(predicted: List, expected: List) -> bool:
    """
   Evaluate room type extraction.
    
    Simplified: just check if the room types are mentioned (not exact match).
    """
    pred_types = set(r.get("room_type") for r in predicted)
    exp_types = set(r.get("room_type") for r in expected if r.get("room_type"))
    
    # At least some overlap
    return len(pred_types & exp_types) > 0 if exp_types else len(pred_types) == 0


def main():
    print("=" * 70)
    print("Entity Extraction Evaluation")
    print("=" * 70)
    
    # Paths
    base_dir = Path(__file__).parent.parent
    test_file = base_dir / "data" / "processed" / "ground_truth_test.jsonl"
    
    # Load test data
    print(f"\nLoading test data from: {test_file}")
    test_data = load_test_data(test_file)
    print(f"[OK] Loaded {len(test_data)} test emails")
    
    # Initialize extractor
    extractor = EntityExtractor()
    
    # Evaluation metrics
    date_metrics = {
        "arrival": {"correct": 0, "total": 0},
        "departure": {"correct": 0, "total": 0},
        "nights": {"correct": 0, "total": 0}
    }
    
    guest_metrics = {
        "adults": {"correct": 0, "total": 0},
        "children_count": {"correct": 0, "total": 0},
        "children_ages": {"correct": 0, "total": 0}
    }
    
    room_metrics = {"correct": 0, "total": 0}
    
    errors = []
    
    print("\n" + "-" * 70)
    print("Evaluating Entity Extraction")
    print("-" * 70)
    
    for i, item in enumerate(test_data, 1):
        email_text = item['raw_email']
        email_id = item.get('email_id', f'email_{i}')
        
        # Get first segment (for now, we're not handling multi-segment yet)
        if not item['segments']:
            continue
        
        expected_segment = item['segments'][0]
        
        # Extract entities
        extracted = extractor.extract(email_text)
        
        # Evaluate dates
        if expected_segment.get('arrival_date') or expected_segment.get('departure_date'):
            date_eval = evaluate_dates(extracted['dates'], expected_segment)
            
            if expected_segment.get('arrival_date'):
                date_metrics['arrival']['total'] += 1
                if date_eval['arrival_correct']:
                    date_metrics['arrival']['correct'] += 1
                else:
                    errors.append({
                        "email_id": email_id,
                        "field": "arrival_date",
                        "expected": expected_segment.get('arrival_date'),
                        "predicted": extracted['dates'].get('arrival_date')
                    })
            
            if expected_segment.get('departure_date'):
                date_metrics['departure']['total'] += 1
                if date_eval['departure_correct']:
                    date_metrics['departure']['correct'] += 1
                else:
                    errors.append({
                        "email_id": email_id,
                        "field": "departure_date",
                        "expected": expected_segment.get('departure_date'),
                        "predicted": extracted['dates'].get('departure_date')
                    })
            
            if expected_segment.get('nights'):
                date_metrics['nights']['total'] += 1
                if date_eval['nights_correct']:
                    date_metrics['nights']['correct'] += 1
        
        # Evaluate guests (check first room for simplicity)
        if expected_segment.get('rooms'):
            expected_room = expected_segment['rooms'][0]
            guest_eval = evaluate_guests(extracted['guests'], expected_room)
            
            if expected_room.get('adults') is not None:
                guest_metrics['adults']['total'] += 1
                if guest_eval['adults_correct']:
                    guest_metrics['adults']['correct'] += 1
                else:
                    errors.append({
                        "email_id": email_id,
                        "field": "adults",
                        "expected": expected_room.get('adults'),
                        "predicted": extracted['guests'].get('adults')
                    })
            
            if expected_room.get('children'):
                guest_metrics['children_count']['total'] += 1
                if guest_eval['children_count_correct']:
                    guest_metrics['children_count']['correct'] += 1
                
                guest_metrics['children_ages']['total'] += 1
                if guest_eval['children_ages_correct']:
                    guest_metrics['children_ages']['correct'] += 1
        
        # Evaluate room types
        if expected_segment.get('rooms'):
            room_metrics['total'] += 1
            if evaluate_room_types(extracted['room_types'], expected_segment['rooms']):
                room_metrics['correct'] += 1
    
    # Print results
    print("\n" + "=" * 70)
    print("Results")
    print("=" * 70)
    
    print("\n### Date Extraction:")
    for field in ['arrival', 'departure', 'nights']:
        metrics = date_metrics[field]
        if metrics['total'] > 0:
            acc = 100 * metrics['correct'] / metrics['total']
            print(f"  {field:15} {metrics['correct']:3}/{metrics['total']:3} ({acc:5.1f}%)")
        else:
            print(f"  {field:15} N/A")
    
    print("\n### Guest Extraction:")
    for field in ['adults', 'children_count', 'children_ages']:
        metrics = guest_metrics[field]
        if metrics['total'] > 0:
            acc = 100 * metrics['correct'] / metrics['total']
            print(f"  {field:20} {metrics['correct']:3}/{metrics['total']:3} ({acc:5.1f}%)")
        else:
            print(f"  {field:20} N/A")
    
    print("\n### Room Type Extraction:")
    if room_metrics['total'] > 0:
        acc = 100 * room_metrics['correct'] / room_metrics['total']
        print(f"  room_types      {room_metrics['correct']:3}/{room_metrics['total']:3} ({acc:5.1f}%)")
    
    # Print some errors
    print("\n" + "=" * 70)
    print(f"Sample Errors (showing first 10 of {len(errors)}):")
    print("=" * 70)
    
    for error in errors[:10]:
        print(f"\n{error['email_id']} - {error['field']}:")
        print(f"  Expected: {error['expected']}")
        print(f"  Predicted: {error['predicted']}")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
