"""
Quick test of GLiNER entity extraction.
Compares GLiNER vs rule-based extraction on sample emails.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.gliner_entities import GLiNEREntityExtractor

# Test samples
test_cases = [
    "Hi, I need a double room from May 12 to May 15, 2026. We are 2 adults.",
    "I'd like to book a room for tonight. Just me.",
    "Booking: 3 nights starting June 1, 2026. 2 adults and 2 kids (ages 5 and 9).",
    "Please reserve a suite for July 10-13. Family of 4 (2 adults, 2 children ages 3 and 7).",
    "I need a single room for tomorrow. One night.",
]

print("=" * 70)
print("GLiNER Entity Extraction Test")
print("=" * 70)
print("\nLoading GLiNER model (this may take a minute)...")

try:
    extractor = GLiNEREntityExtractor(threshold=0.4)
    
    for i, text in enumerate(test_cases, 1):
        print(f"\n{'='*70}")
        print(f"Test {i}:")
        print(f"Text: {text}")
        print(f"\nExtracted:")
        
        result = extractor.extract(text)
        
        # Dates
        dates = result['dates']
        print(f"  Dates:")
        print(f"    Arrival: {dates['arrival_date']} (conf: {dates['confidence']['arrival_date']:.2f})")
        print(f"    Departure: {dates['departure_date']} (conf: {dates['confidence']['departure_date']:.2f})")
        print(f"    Nights: {dates['nights']} (conf: {dates['confidence']['nights']:.2f})")
        
        # Guests
        guests = result['guests']
        print(f"  Guests:")
        print(f"    Adults: {guests['adults']}")
        print(f"    Children: {len(guests['children'])} - {guests['children']}")
        print(f"    Total: {guests['total_guests']}")
        
        # Room types
        rooms = result['room_types']
        print(f"  Room Types: {rooms}")
        
        # Raw entities (for debugging)
        print(f"\n  Raw GLiNER Entities:")
        for ent in result['raw_entities']:
            print(f"    '{ent['text']}' → {ent['label']} (score: {ent['score']:.3f})")

    print("\n" + "=" * 70)
    print("Test Complete!")
    print("=" * 70)

except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
