"""
Evaluate end-to-end pipeline on full test set.
"""

import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.orchestrator import HotelEmailPipeline

print("=" * 70)
print("End-to-End Pipeline Evaluation")
print("=" * 70)

# Load test data
test_file = Path(__file__).parent.parent / "data" / "processed" / "ground_truth_test.jsonl"
print(f"\nLoading test data from: {test_file}")

test_data = []
with open(test_file, 'r', encoding='utf-8') as f:
    for line in f:
        test_data.append(json.loads(line))

print(f"[OK] Loaded {len(test_data)} test emails\n")

# Initialize pipeline
print("Initializing pipeline...")
pipeline = HotelEmailPipeline('config/hotel.yaml')
print("[OK] Pipeline ready\n")

# Evaluation metrics
intent_correct = 0
segment_count_correct = 0
arrival_date_correct = 0
adults_correct = 0
room_type_correct = 0
group_booking_correct = 0

total_booking_requests = 0
total_with_segments = 0

errors = []

print("-" * 70)
print("Running Evaluation")
print("-" * 70 + "\n")

for i, email in enumerate(test_data, 1):
    email_id = email['email_id']
    raw_text = email['raw_email']
    expected_intent = email['intent']
    expected_segments = email.get('segments', [])
    
    # Process through pipeline
    result = pipeline.process(raw_text, email_id=email_id)
    
    # Check intent
    if result['intent'] == expected_intent:
        intent_correct += 1
    
    # Check segment count
    if len(result['segments']) == len(expected_segments):
        segment_count_correct += 1
    
    # For booking requests, check detailed fields
    if expected_intent == 'booking_request' and expected_segments:
        total_booking_requests += 1
        
        # Compare first segment (simplified evaluation)
        if result['segments'] and expected_segments:
            total_with_segments += 1
            pred_seg = result['segments'][0]
            exp_seg = expected_segments[0]
            
            # Arrival date
            if pred_seg.get('arrival_date') == exp_seg.get('arrival_date'):
                arrival_date_correct += 1
            
            # Adults (check first room)
            if pred_seg.get('rooms') and exp_seg.get('rooms'):
                pred_adults = pred_seg['rooms'][0].get('adults')
                exp_adults = exp_seg['rooms'][0].get('adults')
                if pred_adults == exp_adults:
                    adults_correct += 1
                
                # Room type
                pred_room_type = pred_seg['rooms'][0].get('room_type')
                exp_room_type = exp_seg['rooms'][0].get('room_type')
                if pred_room_type == exp_room_type:
                    room_type_correct += 1
            
            # Group booking
            if pred_seg.get('is_group_booking') == exp_seg.get('is_group_booking'):
                group_booking_correct += 1
    
    # Progress indicator
    if i % 10 == 0:
        print(f"Processed {i}/{len(test_data)} emails...")

# Results
print("\n" + "=" * 70)
print("Results")
print("=" * 70)

print(f"\n**Intent Classification**: {intent_correct}/{len(test_data)} ({intent_correct/len(test_data)*100:.1f}%)")
print(f"**Segment Count**: {segment_count_correct}/{len(test_data)} ({segment_count_correct/len(test_data)*100:.1f}%)")

if total_with_segments > 0:
    print(f"\n**Booking Request Fields** (on {total_with_segments} emails with segments):")
    print(f"  - Arrival Date: {arrival_date_correct}/{total_with_segments} ({arrival_date_correct/total_with_segments*100:.1f}%)")
    print(f"  - Adults: {adults_correct}/{total_with_segments} ({adults_correct/total_with_segments*100:.1f}%)")
    print(f"  - Room Type: {room_type_correct}/{total_with_segments} ({room_type_correct/total_with_segments*100:.1f}%)")
    print(f"  - Group Booking: {group_booking_correct}/{total_with_segments} ({group_booking_correct/total_with_segments*100:.1f}%)")

print("\n" + "=" * 70)
print("Evaluation Complete!")
print("=" * 70)
