"""Test guest extraction."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.entities import EntityExtractor

test_cases = [
    "We are 2 adults.",
    "2 adults and 2 kids (ages 5 and 9)",
    "Just me",
    "2 adults, 1 child (age 3)",
    "1 teen (16)",
]

extractor = EntityExtractor()

for text in test_cases:
    result = extractor.extract(text)
    guests = result['guests']
    print(f"Text: {text}")
    print(f"  Adults: {guests['adults']}, Children: {guests['children']}, Total: {guests['total_guests']}")
    print()
