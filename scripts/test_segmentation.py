"""
Test segmentation on multi-segment emails.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.segmentation import EmailSegmenter

# Test cases from new data
test_cases = [
    # email_211: First trip/Second trip pattern
    {
        "text": """Hi,

I need to book accommodations for two separate trips.

First trip: March 10-12, 2026. Single room, just me.
Second trip: April 5-8, 2026. Double room for me and my partner.

Thanks,
Alex""",
        "expected_segments": 2
    },
    # email_214: Numbered list with 3 items
    {
        "text": """Hi Team,

Please process the following reservations:

1. May 12-14, 2026: Single room for Mr. Doe.
2. June 20-25, 2026: Deluxe room for Mrs. Smith.
3. July 1-2, 2026: Twin room for Mr. Jones.

Charge to the company card.""",
        "expected_segments": 3
    },
    # email_217: "Also" separator
    {
        "text": """Hi,

I'd like to book a room for myself for July 1-5, 2026. Standard double.

Also, I need to book a separate room for my colleague who is visiting later, from August 1-5, 2026. Single room for him.

Cheers.""",
        "expected_segments": 2
    },
    # email_224: "Furthermore" separator
    {
        "text": """Hi,

We need a family room for June 1-7, 2026. 2 adults, 2 kids.

Furthermore, my parents are joining for the weekend. We need a separate double room for them for June 5-7, 2026.""",
        "expected_segments": 2
    },
]

print("=" * 70)
print("Multi-Segment Email Detection Test")
print("=" * 70)

segmenter = EmailSegmenter()

for i, test in enumerate(test_cases, 1):
    print(f"\nTest {i}:")
    print(f"Expected segments: {test['expected_segments']}")
    
    segments = segmenter.segment(test['text'])
    
    print(f"Detected segments: {len(segments)}")
    print(f"Method: {segments[0]['method'] if segments else 'none'}")
    
    for seg in segments:
        print(f"\n  Segment {seg['segment_id']}:")
        # Show first 80 chars of text
        preview = seg['text'].replace('\n', ' ')[:80]
        print(f"    Text preview: {preview}...")
    
    # Check result
    if len(segments) == test['expected_segments']:
        print(f"\nResult: PASS")
    else:
        print(f"\nResult: FAIL (expected {test['expected_segments']}, got {len(segments)})")
    
    print("-" * 70)

print("\n" + "=" * 70)
print("Test Complete!")
print("=" * 70)
