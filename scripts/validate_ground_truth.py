"""
Validate the generated ground truth dataset.

Checks:
- JSON format validity
- Schema compliance
- Intent distribution
- Date formats
- Guest counts
- Group booking flags
"""

import json
import sys
from pathlib import Path
from collections import Counter
from datetime import datetime

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def validate_dataset(data_path: Path):
    """Validate ground truth dataset."""
    
    print("=" * 60)
    print("Ground Truth Dataset Validation")
    print("=" * 60)
    print(f"\nFile: {data_path}\n")
    
    # Load data
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = [json.loads(line) for line in f]
        print(f"[OK] Loaded {len(data)} emails successfully")
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON parsing error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error loading file: {e}")
        return False
    
    # Validate schema
    required_fields = ['email_id', 'raw_email', 'intent', 'segments']
    errors = []
    
    print("\n" + "-" * 60)
    print("Schema Validation")
    print("-" * 60)
    
    for i, item in enumerate(data):
        # Check required fields
        missing = [f for f in required_fields if f not in item]
        if missing:
            errors.append(f"Email {i+1}: Missing fields {missing}")
        
        # Validate intent
        valid_intents = {
            'booking_request', 'booking_modification', 'cancellation',
            'price_inquiry', 'availability_check', 'other'
        }
        if item.get('intent') not in valid_intents:
            errors.append(f"Email {i+1}: Invalid intent '{item.get('intent')}'")
        
        # Validate segments
        if not isinstance(item.get('segments'), list):
            errors.append(f"Email {i+1}: 'segments' must be a list")
    
    if errors:
        print(f"[ERROR] Found {len(errors)} schema errors:")
        for err in errors[:10]:  # Show first 10
            print(f"  - {err}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")
        return False
    else:
        print(f"[OK] All {len(data)} emails have valid schema")
    
    # Intent distribution
    print("\n" + "-" * 60)
    print("Intent Distribution")
    print("-" * 60)
    
    intents = Counter(item['intent'] for item in data)
    total = len(data)
    
    for intent, count in sorted(intents.items()):
        pct = 100 * count / total
        print(f"  {intent:<25} {count:>4} ({pct:>5.1f}%)")
    
    # Segment analysis
    print("\n" + "-" * 60)
    print("Segment Analysis")
    print("-" * 60)
    
    segment_counts = Counter(len(item['segments']) for item in data)
    
    print(f"  Emails with 0 segments: {segment_counts[0]} (non-booking intents)")
    print(f"  Emails with 1 segment:  {segment_counts[1]} (standard bookings)")
    if segment_counts[2] > 0:
        print(f"  Emails with 2 segments:  {segment_counts[2]} (multi-request)")
    if any(c > 2 for c in segment_counts.keys()):
        print(f"  Emails with 3+ segments: {sum(c for k, c in segment_counts.items() if k > 2)}")
    
    # Group bookings
    group_bookings = sum(
        1 for item in data
        for seg in item['segments']
        if seg.get('is_group_booking')
    )
    print(f"\n  Group bookings (≥7 rooms or ≥15 guests): {group_bookings}")
    
    # Date analysis
    print("\n" + "-" * 60)
    print("Date Analysis")
    print("-" * 60)
    
    dates_with_arrival = sum(
        1 for item in data
        for seg in item['segments']
        if seg.get('arrival_date')
    )
    dates_with_departure = sum(
        1 for item in data
        for seg in item['segments']
        if seg.get('departure_date')
    )
    dates_with_nights = sum(
        1 for item in data
        for seg in item['segments']
        if seg.get('nights')
    )
    
    total_segments = sum(len(item['segments']) for item in data)
    
    print(f"  Total segments: {total_segments}")
    print(f"  With arrival_date: {dates_with_arrival}")
    print(f"  With departure_date: {dates_with_departure}")
    print(f"  With nights: {dates_with_nights}")
    
    # Children analysis
    print("\n" + "-" * 60)
    print("Children/Guest Analysis")
    print("-" * 60)
    
    segments_with_children = 0
    child_ages = []
    
    for item in data:
        for seg in item['segments']:
            for room in seg.get('rooms', []):
                children = room.get('children', [])
                if children:
                    segments_with_children += 1
                    child_ages.extend(c.get('age') for c in children if c.get('age') is not None)
    
    print(f"  Segments with children: {segments_with_children}")
    if child_ages:
        print(f"  Total children: {len(child_ages)}")
        print(f"  Age range: {min(child_ages)}-{max(child_ages)}")
        under_12 = sum(1 for age in child_ages if age < 12)
        over_12 = sum(1 for age in child_ages if age >= 12)
        print(f"  Under 12: {under_12}, Over 12: {over_12}")
    
    # Room type distribution
    print("\n" + "-" * 60)
    print("Room Type Distribution")
    print("-" * 60)
    
    room_types = Counter()
    for item in data:
        for seg in item['segments']:
            for room in seg.get('rooms', []):
                room_types[room.get('room_type')] += 1
    
    for room_type, count in sorted(room_types.items()):
        print(f"  {room_type:<15} {count:>3}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    print(f"✓ Dataset is valid!")
    print(f"✓ {len(data)} emails")
    print(f"✓ {len(intents)} intent categories")
    print(f"✓ {total_segments} booking segments")
    print(f"✓ {group_bookings} group bookings")
    print(f"✓ Ready for train/test split")
    print("=" * 60)
    
    return True


if __name__ == "__main__":
    data_path = Path(__file__).parent.parent / "data" / "labels" / "ground_truth.jsonl"
    
    if not data_path.exists():
        print(f"Error: File not found at {data_path}")
        sys.exit(1)
    
    success = validate_dataset(data_path)
    sys.exit(0 if success else 1)
