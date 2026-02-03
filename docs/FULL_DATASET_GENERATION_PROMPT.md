# Full Ground Truth Dataset Generation Prompt

Use this prompt with any LLM (GPT-4, Claude 3.5, Gemini 1.5 Pro, etc.) to generate 200+ hotel booking emails with complete ground truth annotations.

---

## PROMPT START

I need you to generate 200 synthetic hotel booking emails with **COMPLETE ground truth annotations** for training an NLP pipeline. Each email needs raw text PLUS structured entity labels.

### Output Format (CRITICAL):

Output **JSONL format** (one JSON object per line). Each line must match this exact schema:

```json
{
  "email_id": "email_XXX",
  "raw_email": "Full email text with signatures, greetings, etc.",
  "intent": "booking_request",
  "segments": [
    {
      "segment_id": 0,
      "arrival_date": "2026-05-12",
      "departure_date": "2026-05-15",
      "nights": 3,
      "rooms": [
        {
          "room_type": "double",
          "quantity": 1,
          "adults": 2,
          "children": [{"age": 5}, {"age": 9}],
          "total_guests": 4
        }
      ],
      "is_group_booking": false
    }
  ]
}
```

### Schema Fields Explained:

**Top Level:**
- `email_id`: Unique ID like "email_001", "email_002", etc.
- `raw_email`: The complete email text (include signatures, greetings, subject lines)
- `intent`: One of: `booking_request`, `booking_modification`, `cancellation`, `price_inquiry`, `availability_check`, `other`
- `segments`: List of booking segments (usually 1, can be 2+ for multi-request emails)

**Segment Fields:**
- `segment_id`: Integer starting at 0
- `arrival_date`: ISO format "YYYY-MM-DD" (or null if not mentioned)
- `departure_date`: ISO format "YYYY-MM-DD" (or null if not mentioned)
- `nights`: Integer (or null if not mentioned)
- `rooms`: List of room configurations
- `is_group_booking`: true if ≥7 rooms OR ≥15 total guests

**Room Fields:**
- `room_type`: One of: `single`, `double`, `twin`, `suite`, `family`, `deluxe`, `standard`, `king`, `queen`
- `quantity`: Number of rooms of this type
- `adults`: Number of adults
- `children`: List of child objects with `age` field
- `total_guests`: Sum of adults + children

### Important Rules:

1. **Dates**: Use year 2026 or 2027, realistic dates
2. **Children ages**: Ages 0-17, mix of under/over 12 (threshold for adult classification)
3. **Group bookings**: Must have `is_group_booking: true` if ≥7 rooms OR ≥15 guests
4. **Multi-segment**: ~5% should have 2 segments (two separate booking requests in one email)
5. **Missing data**: Use `null` for fields not mentioned (e.g., if only nights mentioned, arrival/departure are null)
6. **Room types**: Use standard types listed above (can add aliases like "king bed" → "king")

### Email Diversity Requirements:

**Content variety:**
- Include Subject lines in ~30% of emails
- Add email signatures in ~40% ("Sent from my iPhone", "Best regards, Name")
- Add greetings in ~50% ("Hi", "Hello", "Good morning")
- Include disclaimers in ~10% ("CONFIDENTIAL: This email...")
- Vary tone: formal, casual, brief, verbose, friendly, demanding
- Mix lengths: 50 chars to 500+ chars
- Add typos/informal language in ~20%

**Date formats (vary these in raw_email text):**
- Absolute: "May 12-15, 2026", "12/05/2026 to 15/05/2026"
- Relative: "next Friday", "this weekend", "arriving tomorrow"
- With nights: "3 nights starting June 1st", "staying 4 nights from July 10"

**Guest configurations:**
- Adults only: "2 adults", "just me", "solo traveler"
- With children: "2 adults and 2 kids (ages 5 and 9)"
- Mixed ages: Include children ages 11-13 (testing age threshold)
- Groups: "10 guests", "15 people for conference"

**Booking scenarios to include:**
- Simple: Standard booking with clear dates
- Complex: Multiple rooms, children, special requests
- Last-minute: "tonight", "same-day"
- Extended: "2 weeks", "30 days"
- Group: Conferences, weddings, family reunions (7+ rooms)
- Ambiguous: Vague dates like "sometime in spring"
- Special requests: Wheelchair access, pet-friendly, quiet room

### Intent Distribution (for 200 emails):

- `booking_request`: 110-120 emails (~55-60%)
- `booking_modification`: 24-30 emails (~12-15%)
- `cancellation`: 16-20 emails (~8-10%)
- `price_inquiry`: 16-20 emails (~8-10%)
- `availability_check`: 16-20 emails (~8-10%)
- `other`: 10-14 emails (~5-7%)

### Examples:

**Example 1: Simple Booking**
```json
{"email_id": "email_001", "raw_email": "Hi there,\n\nI need a double room from May 12 to May 15, 2026 for 2 adults.\n\nThanks!", "intent": "booking_request", "segments": [{"segment_id": 0, "arrival_date": "2026-05-12", "departure_date": "2026-05-15", "nights": 3, "rooms": [{"room_type": "double", "quantity": 1, "adults": 2, "children": [], "total_guests": 2}], "is_group_booking": false}]}
```

**Example 2: Family with Children**
```json
{"email_id": "email_002", "raw_email": "Subject: Family Vacation\n\nHello,\n\nWe'd like to book a suite for July 10-13, 2026. We are 2 adults and 2 children (ages 6 and 11).\n\nBest regards,\nSarah", "intent": "booking_request", "segments": [{"segment_id": 0, "arrival_date": "2026-07-10", "departure_date": "2026-07-13", "nights": 3, "rooms": [{"room_type": "suite", "quantity": 1, "adults": 2, "children": [{"age": 6}, {"age": 11}], "total_guests": 4}], "is_group_booking": false}]}
```

**Example 3: Cancellation (no segments)**
```json
{"email_id": "email_003", "raw_email": "Please cancel my booking. Reservation #ABC123.\n\nThanks.", "intent": "cancellation", "segments": []}
```

**Example 4: Price Inquiry (no segments)**
```json
{"email_id": "email_004", "raw_email": "How much is a king suite for the weekend of August 5th?", "intent": "price_inquiry", "segments": []}
```

**Example 5: Group Booking (≥7 rooms)**
```json
{"email_id": "email_005", "raw_email": "Hi,\n\nWe need 10 double rooms for a conference from June 20-22, 2026.\n\nBest,\nJohn", "intent": "booking_request", "segments": [{"segment_id": 0, "arrival_date": "2026-06-20", "departure_date": "2026-06-22", "nights": 2, "rooms": [{"room_type": "double", "quantity": 10, "adults": 20, "children": [], "total_guests": 20}], "is_group_booking": true}]}
```

**Example 6: Multi-Segment (2 requests in 1 email)**
```json
{"email_id": "email_006", "raw_email": "Hi,\n\nI need a room from July 5-7 and also another booking from August 12-14. Both for 2 adults.\n\nThanks!", "intent": "booking_request", "segments": [{"segment_id": 0, "arrival_date": "2026-07-05", "departure_date": "2026-07-07", "nights": 2, "rooms": [{"room_type": "double", "quantity": 1, "adults": 2, "children": [], "total_guests": 2}], "is_group_booking": false}, {"segment_id": 1, "arrival_date": "2026-08-12", "departure_date": "2026-08-14", "nights": 2, "rooms": [{"room_type": "double", "quantity": 1, "adults": 2, "children": [], "total_guests": 2}], "is_group_booking": false}]}
```

**Example 7: Relative Dates (use null for unknown dates)**
```json
{"email_id": "email_007", "raw_email": "I need a room for next weekend. Just 1 person.", "intent": "booking_request", "segments": [{"segment_id": 0, "arrival_date": null, "departure_date": null, "nights": 2, "rooms": [{"room_type": "single", "quantity": 1, "adults": 1, "children": [], "total_guests": 1}], "is_group_booking": false}]}
```

### Critical Format Requirements:

1. **ONLY output JSONL** - one complete JSON object per line
2. **NO explanations, NO markdown blocks, NO text before/after**
3. **Valid JSON** - escape quotes with \", newlines with \n
4. **Sequential IDs** - email_001, email_002, ..., email_200
5. **ISO dates** - Always "YYYY-MM-DD" format for dates
6. **Empty segments** - Use `[]` for intents with no booking details (cancellation, price_inquiry, etc.)

### Start Generating:

Generate 200 emails following the rules above. Output ONLY the JSONL data, nothing else.

## PROMPT END

---

## How to Use:

1. **Copy the prompt** (from PROMPT START to PROMPT END)
2. **Paste into LLM** (GPT-4, Claude, Gemini recommended)
3. **Generate in batches**:
   - Batch 1: Ask for 70 emails
   - Batch 2: Ask for 70 emails
   - Batch 3: Ask for 60 emails
4. **Combine outputs** into one file: `data/labels/ground_truth_full.jsonl`
5. **Validate format** (I'll create a validation script)

### Pro Tips:

**If LLM adds markdown:**
Remove the ```jsonl and ``` wrappers

**If LLM generates explanations:**
Re-prompt: "ONLY output JSONL, no explanations, no text before or after the data"

**For best quality:**
- Use GPT-4 or Claude 3.5 Sonnet (best at following complex schemas)
- Generate in smaller batches (50-70 at a time)
- Validate each batch before continuing

---

## What I'll Do Next:

Once you provide `data/labels/ground_truth_full.jsonl`:

1. ✅ **Validate the data** (check schema, dates, consistency)
2. ✅ **Create new train/test split** (160 train / 40 test)
3. ✅ **Update all scripts** to use new data
4. ✅ **Retrain intent classifier** (much better results expected!)
5. ✅ **Ready for Phase 4** (entity extraction with real data)

---

## Expected File Location:

Save the generated data to:
```
data/labels/ground_truth_full.jsonl
```

Size: ~200-300 KB for 200 emails
