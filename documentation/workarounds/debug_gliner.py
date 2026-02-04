"""Debug GLiNER extraction with lower threshold and detailed output."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from gliner import GLiNER

# Test with a simple case
test_text = "I need a double room from May 12 to May 15, 2026. 2 adults."

print("Loading GLiNER model...")
model = GLiNER.from_pretrained("urchade/gliner_medium-v2.1")
print("Model loaded!\n")

# Test with different thresholds
labels = [
    "arrival date",
    "check-in date",
    "departure date",
    "check-out date",
    "number of nights",
    "number of adults",
    "number of guests",
    "number of children",
    "child age",
    "room type",
    "hotel name"
]

print(f"Text: {test_text}\n")
print("=" * 70)

for threshold in [0.1, 0.2, 0.3, 0.4, 0.5]:
    print(f"\nThreshold: {threshold}")
    entities = model.predict_entities(test_text, labels, threshold=threshold)
    
    if entities:
        for ent in entities:
            print(f"  '{ent['text']}' -> {ent['label']} (score: {ent['score']:.3f})")
    else:
        print("  No entities found")

print("\n" + "=" * 70)
print("\nTrying with simpler/broader labels...")

simple_labels = ["date", "number", "room", "person"]
entities = model.predict_entities(test_text, simple_labels, threshold=0.1)

if entities:
    for ent in entities:
        print(f"  '{ent['text']}' -> {ent['label']} (score: {ent['score']:.3f})")
else:
    print("  No entities found")
