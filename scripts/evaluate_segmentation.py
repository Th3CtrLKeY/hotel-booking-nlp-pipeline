"""
Evaluate segmentation accuracy on test set.
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.segmentation import EmailSegmenter

print("=" * 70)
print("Segmentation Evaluation")
print("=" * 70)

# Load test data
test_file = Path(__file__).parent.parent / "data" / "processed" / "ground_truth_test.jsonl"
print(f"\nLoading test data from: {test_file}")

test_data = []
with open(test_file, 'r', encoding='utf-8') as f:
    for line in f:
        test_data.append(json.loads(line))

print(f"[OK] Loaded {len(test_data)} test emails\n")

# Initialize segmenter
segmenter = EmailSegmenter()

# Evaluation metrics
correct_count = 0
total_count = 0
errors = []

print("-" * 70)
print("Evaluating Segmentation")
print("-" * 70 + "\n")

for email in test_data:
    email_id = email['email_id']
    text = email['raw_email']
    intent = email['intent']
    expected_segments = len(email.get('segments', []))
    
    # Segment (with intent awareness)
    detected = segmenter.segment(text, intent=intent)
    detected_count = len(detected)
    
    total_count += 1
    
    if detected_count == expected_segments:
        correct_count += 1
    else:
        errors.append({
            "email_id": email_id,
            "expected": expected_segments,
            "detected": detected_count,
            "method": detected[0]['method'] if detected else 'none'
        })

# Results
accuracy = (correct_count / total_count * 100) if total_count > 0 else 0

print("=" * 70)
print("Results")
print("=" * 70)
print(f"\nSegment Count Accuracy: {correct_count}/{total_count} ({accuracy:.1f}%)\n")

if errors:
    print(f"Errors: {len(errors)}")
    print("\nSample Errors (showing first 5):")
    for error in errors[:5]:
        print(f"\n{error['email_id']}:")
        print(f"  Expected segments: {error['expected']}")
        print(f"  Detected segments: {error['detected']}")
        print(f"  Method: {error['method']}")

print("\n" + "=" * 70)
print(f"Evaluation Complete!")
print("=" * 70)
