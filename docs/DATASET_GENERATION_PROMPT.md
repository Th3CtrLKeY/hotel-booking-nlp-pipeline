# LLM Prompt for Generating Hotel Email Dataset

Copy and paste this prompt to an LLM (GPT-4, Claude, Gemini, etc.) to generate synthetic hotel booking emails for training the intent classifier.

---

## PROMPT START

I need you to generate 100 synthetic hotel booking emails with labeled intents for training a machine learning classifier. These should be realistic, diverse emails that customers might send to a hotel.

### Intent Categories (6 total):

1. **booking_request** - New booking inquiries (most common, ~60-70%)
2. **booking_modification** - Requests to change existing bookings (~10-15%)
3. **cancellation** - Cancellation requests (~5-10%)
4. **price_inquiry** - Questions about pricing/rates (~5-10%)
5. **availability_check** - Checking room availability (~5-10%)
6. **other** - Unrelated inquiries or complaints (~5%)

### Email Characteristics:

**Vary these elements for realism:**
- **Tone**: Formal, casual, brief, verbose, friendly, demanding
- **Guest types**: Business travelers, families, couples, groups, solo
- **Booking details**: Dates (absolute, relative), room types, guest counts, special requests
- **Language**: Simple, complex, grammatically imperfect, typos
- **Length**: Short (1-2 sentences) to long (multiple paragraphs)
- **Signatures**: Some with "Sent from my iPhone", "Best regards + name", etc.
- **Extra content**: Some with disclaimers, greetings, email threads

**Room types to use (randomly):**
- Single, double, twin, suite, family room, deluxe, standard, king bed, queen bed

**Date formats to vary:**
- Absolute: "May 12-15, 2026", "12/05/2026 to 15/05/2026"
- Relative: "next Friday", "this weekend", "arriving tomorrow"
- With nights: "3 nights starting June 1st"

**Guest configurations:**
- Adults only: "2 adults", "just me"
- With children: "2 adults and 2 kids (ages 5 and 9)"
- Groups: "10 guests", "conference attendees"

### Example Emails (for reference):

**booking_request:**
```
Subject: Room needed

Hi, I need a double room from May 12 to May 15, 2026 for 2 adults. Please let me know if you have availability.

Thanks!
```

**booking_modification:**
```
I need to change my reservation for April 20th. Can we move it to April 21st instead? Confirmation #12345.
```

**cancellation:**
```
Please cancel my booking for June 5-7. Reservation number ABC123.
```

**price_inquiry:**
```
How much is a double room for the weekend of July 4th? Looking for best rate.
```

**availability_check:**
```
Do you have any king suites available from August 1-5 for 2 guests?
```

### Required Output Format:

**CRITICAL**: Output ONLY valid JSONL (JSON Lines format). Each line must be a complete JSON object.

Format each email as:
```jsonl
{"text": "Email content here...", "intent": "booking_request"}
{"text": "Another email...", "intent": "cancellation"}
```

**Rules:**
1. One JSON object per line (JSONL format)
2. Each object has exactly 2 fields: "text" and "intent"
3. "text" contains the full email (can include newlines as \n)
4. "intent" is one of the 6 categories listed above
5. Escape quotes inside text with \"
6. NO markdown code blocks, NO explanations, ONLY raw JSONL output

### Distribution Target:

- booking_request: 60-70 emails
- booking_modification: 10-15 emails
- cancellation: 8-12 emails
- price_inquiry: 8-12 emails
- availability_check: 8-12 emails
- other: 5-8 emails

**Total: 100 emails**

### Diversity Requirements:

- Include various date ranges (near future, far future, past dates in modifications)
- Mix simple and complex bookings
- Include edge cases: same-day bookings, long stays, group bookings
- Add realistic noise: typos, informal language, multiple requests in one email
- Some emails should have extra content (signatures, disclaimers, greetings)
- Vary lengths significantly (50 chars to 500+ chars)

### Start generating now:

Output 100 JSONL lines, no explanations, just the data.

## PROMPT END

---

## How to Use:

1. **Copy the prompt above** (from "PROMPT START" to "PROMPT END")
2. **Paste into an LLM** (GPT-4, Claude 3.5, Gemini 1.5 Pro, etc.)
3. **Copy the JSONL output** to a file: `data/processed/intent_train_augmented.jsonl`
4. **Verify format** with:
   ```powershell
   python -c "import json; [json.loads(line) for line in open('data/processed/intent_train_augmented.jsonl')]"
   ```
5. **Retrain the model**:
   ```powershell
   python scripts/train_intent_classifier.py
   ```

---

## Tips for Best Results:

### If using GPT-4/Claude:
- May need to prompt in 2-3 batches (e.g., "Generate first 50", then "Generate next 50")
- Ask to verify JSONL format if output has errors

### If using Gemini:
- Works well with full 100-email generation
- Very good at following JSONL format

### If LLM adds markdown blocks:
Just remove the triple backticks and "```jsonl" / "```" wrappers

### Common Issues:

**Problem**: LLM adds explanations
**Solution**: Re-prompt with "ONLY output JSONL, no text before or after"

**Problem**: JSON parsing errors
**Solution**: Check for unescaped quotes, missing commas, or invalid UTF-8

**Problem**: Unbalanced intent distribution
**Solution**: Count intents and ask LLM to generate more of specific types

---

## Validation Script:

After generating, validate with this script:

```python
import json
from collections import Counter

# Load data
with open('data/processed/intent_train_augmented.jsonl', 'r') as f:
    data = [json.loads(line) for line in f]

# Count intents
intents = Counter(item['intent'] for item in data)

print(f"Total emails: {len(data)}")
print("\nIntent distribution:")
for intent, count in sorted(intents.items()):
    print(f"  {intent}: {count}")

# Check for valid intents
valid_intents = {'booking_request', 'booking_modification', 'cancellation', 
                 'price_inquiry', 'availability_check', 'other'}
invalid = [item for item in data if item['intent'] not in valid_intents]
if invalid:
    print(f"\nWARNING: {len(invalid)} emails with invalid intents!")
else:
    print("\n✓ All intents are valid!")
```

Save as `scripts/validate_dataset.py` and run:
```powershell
python scripts/validate_dataset.py
```

---

## Expected Improvement:

With 100 training emails (vs current 17), you should see:

**Before (current)**:
- Training accuracy: 88%
- Test accuracy: 50% (severe overfitting)

**After (with 100 emails)**:
- Training accuracy: 90-95%
- Test accuracy: 80-90% (much better generalization)
- All intents properly learned (not just booking_request)

---

## Alternative: Combine Original + Generated

To keep your hand-crafted examples:

```powershell
# Combine original training data with generated data
cat data/processed/intent_train.jsonl data/processed/intent_train_augmented.jsonl > data/processed/intent_train_combined.jsonl

# Retrain with combined dataset
python scripts/train_intent_classifier.py
```

This gives you 117 total training emails (17 original + 100 generated).
