# Experimental Files - Phase 4 Entity Extraction

This folder contains experimental scripts and implementations from Phase 4 that were tested but not included in the final production solution.

---

## GLiNER-Based Approach (Rejected)

### `gliner_entities.py`
**Purpose**: Zero-shot NER implementation using GLiNER model (`urchade/gliner_medium-v2.1`)

**What it does**: Attempts to extract booking entities (dates, guests, room types) using pre-trained GLiNER model with custom labels

**Why rejected**: 
- Very low confidence scores (0.20-0.27)
- Noisy extractions (random words identified as entities)
- Poor domain fit for numerical/booking entities
- 10-20x slower than rule-based approach
- Performance worse than simple rules

**Dependencies**: `gliner==0.2.24`, `onnxruntime`

---

### `test_gliner.py`
**Purpose**: Test script for GLiNER entity extraction

**What it does**: Tests GLiNER on 5 sample booking emails and displays extracted entities with confidence scores

**Findings**: Model extracted zero usable entities at threshold 0.4+

---

### `debug_gliner.py`
**Purpose**: Debug GLiNER extraction with various thresholds

**What it does**: Tests GLiNER at different confidence thresholds (0.1-0.5) and with different label sets

**Key Discovery**: Only found entities at threshold <0.3, with nonsensical results:
```
"I" → number of guests (0.220)
"room" → number of guests (0.245)
"12" → number of nights (0.251)
```

---

## Early Testing Scripts

### `test_date_extraction.py`
**Purpose**: Unit tests for initial date extraction implementation

**What it does**: Tests date extraction on 3 sample cases before full evaluation

**Status**: Superseded by `evaluate_entity_extraction.py` (full test set)

---

### `test_guest_extraction.py`
**Purpose**: Unit tests for guest count extraction

**What it does**: Tests adult and children extraction on 5 sample cases

**Issue Found**: Children ages not parsing correctly for "ages 5 and 9" pattern (due to "and" word)

**Status**: Superseded by full evaluation

---

### `test_improved_extraction.py`
**Purpose**: Validation tests for rule improvements (implicit adults, date ranges)

**What it does**: Tests 4 specific cases that were failing before improvements

**Results**: 3/4 passing after improvements (adults extraction improved 35% → 61%)

**Status**: Kept for regression testing

---

## Lessons Learned

1. **Pre-trained ML models aren't always better**: GLiNER showed worse performance than hand-crafted rules for this domain

2. **Zero-shot doesn't mean no-effort**: Still requires significant experimentation and domain adaptation

3. **Incremental testing is valuable**: Small test scripts helped identify specific issues quickly

4. **Rules work well for structured domains**: Hotel bookings have predictable patterns ideal for regex + dateparser

---

## Final Production Approach

**File**: `pipeline/entities.py`

**Method**: Enhanced rule-based extraction with:
- dateparser for natural language dates
- Regex patterns for guests and room types
- Implicit adult defaults (1 adult for "book a room")
- Date arithmetic (arrival + nights → departure)

**Performance**: 60-83% accuracy across core fields

---

**Note**: These files are retained for historical reference and to document the development process. They are not used in production.
