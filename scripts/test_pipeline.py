"""
Test end-to-end pipeline on sample emails.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.orchestrator import HotelEmailPipeline
import json

print("=" * 70)
print("End-to-End Pipeline Test")
print("=" * 70)

# Initialize pipeline
pipeline = HotelEmailPipeline('config/hotel.yaml')

# Test cases
test_cases = [
    {
        "name": "Simple booking",
        "email": """Hi,

I would like to book a double room for the weekend of May 15-17, 2026. We are 2 adults.

Thanks,
John""",
        "expected": {
            "intent": "booking_request",
            "segments": 1,
            "is_group": False
        }
    },
    {
        "name": "Multi-segment booking",
        "email": """Hi,

I need to book accommodations for two separate trips.

First trip: March 10-12, 2026. Single room, just me.
Second trip: April 5-8, 2026. Double room for me and my partner.

Thanks,
Alex""",
        "expected": {
            "intent": "booking_request",
            "segments": 2,
            "is_group": False
        }
    },
    {
        "name": "Group booking (>= 4 rooms)",
        "email": """Hello,

We are looking to host our corporate retreat at your hotel. We need 15 single rooms for 15 guests from September 1st to September 5th, 2026.

Best,
HR Team""",
        "expected": {
            "intent": "booking_request",
            "segments": 1,
            "is_group": True
        }
    },
    {
        "name": "Group booking (>= 12 guests)",
        "email": """I'd like to book 3 rooms for my team. 14 adults total. May 10-12, 2026.""",
        "expected": {
            "intent": "booking_request",
            "segments": 1,
            "is_group": True
        }
    },
    {
        "name": "Cancellation (no segments)",
        "email": "Please cancel my reservation #88421 immediately.",
        "expected": {
            "intent": "cancellation",
            "segments": 0
        }
    }
]

print("\nRunning tests...")
print("=" * 70 + "\n")

passed = 0
failed = 0

for i, test in enumerate(test_cases, 1):
    print(f"Test {i}: {test['name']}")
    print("-" * 70)
    
    # Process email
    result = pipeline.process(test['email'])
    
    # Display result
    print(f"Intent: {result['intent']}")
    print(f"Segments: {len(result.get('segments', []))}")
    
    for seg in result.get('segments', []):
        print(f"\n  Segment {seg['segment_id']}:")
        print(f"    Arrival: {seg.get('arrival_date')}")
        print(f"    Nights: {seg.get('nights')}")
        print(f"    Rooms: {len(seg.get('rooms', []))}")
        print(f"    Group: {seg.get('is_group_booking')}")
        
        for room in seg.get('rooms', []):
            print(f"      - {room.get('room_type')}: {room.get('quantity')}x, "
                  f"{room.get('adults')} adults, {len(room.get('children', []))} children")
    
    # Check expectations
    checks = []
    checks.append(result['intent'] == test['expected']['intent'])
    checks.append(len(result.get('segments', [])) == test['expected']['segments'])
    
    if test['expected'].get('is_group') is not None and result.get('segments'):
        checks.append(result['segments'][0]['is_group_booking'] == test['expected']['is_group'])
    
    if all(checks):
        print(f"\nResult: PASS")
        passed += 1
    else:
        print(f"\nResult: FAIL")
        failed += 1
    
    print("=" * 70 + "\n")

# Summary
print(f"Tests passed: {passed}/{passed + failed}")
print("=" * 70)
