"""Test improved entity extraction on sample cases."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.entities import EntityExtractor

# Test cases that were failing before
test_cases = [
    {
        "text": "Hi, I need a double room from May 12 to May 15, 2026. We are 2 adults.",
        "expected": {"arrival": "2026-05-12", "departure": "2026-05-15", "adults": 2}
    },
    {
        "text": "I need a room for tonight.",
        "expected": {"adults": 1}  # Should default to 1
    },
    {
        "text": "Please book a room.",
        "expected": {"adults": 1}  # Should default to 1
    },
    {
        "text": "Reserve a single room for me.",
        "expected": {"adults": 1}
    },
]

print("=" * 70)
print("Testing Improved Entity Extraction")
print("=" * 70)

extractor = EntityExtractor()

for i, test in enumerate(test_cases, 1):
    print(f"\nTest {i}:")
    print(f"Text: {test['text']}")
    
    result = extractor.extract(test['text'])
    dates = result['dates']
    guests = result['guests']
    
    print(f"\nExtracted:")
    print(f"  Dates: arrival={dates['arrival_date']}, departure={dates['departure_date']}")
    print(f"  Guests: adults={guests['adults']}, children={len(guests['children'])}")
    
    print(f"\nExpected:")
    expected = test['expected']
    if 'arrival' in expected:
        print(f"  Dates: arrival={expected.get('arrival')}, departure={expected.get('departure')}")
    if 'adults' in expected:
        print(f"  Guests: adults={expected['adults']}")
    
    # Check if it matches
    match = True
    if 'arrival' in expected and dates['arrival_date'] != expected['arrival']:
        match = False
    if 'adults' in expected and guests['adults'] != expected['adults']:
        match = False
    
    print(f"\nResult: {'PASS' if match else 'FAIL'}")
    print("-" * 70)

print("\n" + "=" * 70)
