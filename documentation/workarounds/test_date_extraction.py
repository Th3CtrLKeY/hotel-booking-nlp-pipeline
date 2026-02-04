"""
Quick test of date extraction functionality.
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.entities import EntityExtractor

# Test samples
test_cases = [
    {
        "text": "Hi, I need a double room from May 12 to May 15, 2026. We are 2 adults.",
        "expected": {
            "arrival": "2026-05-12",
            "departure": "2026-05-15",
            "nights": 3
        }
    },
    {
        "text": "I'd like to book a room for tonight. Just me.",
        "expected": {
            "arrival": None,  # Relative date
            "nights": 1
        }
    },
    {
        "text": "Booking: 3 nights starting June 1, 2026.",
        "expected": {
            "arrival": "2026-06-01",
            "nights": 3
        }
    }
]

print("=" * 60)
print("Date Extraction Test")
print("=" * 60)

extractor = EntityExtractor()

for i, test in enumerate(test_cases, 1):
    print(f"\nTest {i}:")
    print(f"Text: {test['text'][:70]}...")
    
    result = extractor.extract(test['text'])
    dates = result['dates']
    
    print(f"Extracted:")
    print(f"  Arrival: {dates['arrival_date']} (conf: {dates['confidence']['arrival_date']:.2f})")
    print(f"  Departure: {dates['departure_date']} (conf: {dates['confidence']['departure_date']:.2f})")
    print(f"  Nights: {dates['nights']} (conf: {dates['confidence']['nights']:.2f})")

print("\n" + "=" * 60)
