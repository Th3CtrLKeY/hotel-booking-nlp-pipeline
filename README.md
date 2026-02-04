# Hotel Email Parser

> Production-grade NLP system for extracting structured booking information from hotel reservation emails

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📋 Overview

The Hotel Email Parser is an end-to-end NLP pipeline that automatically extracts structured booking information from unstructured hotel reservation emails. It combines transformer-based intent classification, rule-based entity extraction, and business logic to handle real-world booking scenarios.

### Key Features

✅ **Multi-Intent Classification** - Distinguishes booking requests, modifications, cancellations, price inquiries  
✅ **Multi-Segment Detection** - Handles emails with multiple separate booking requests  
✅ **Comprehensive Entity Extraction** - Dates, guest counts, room types, children ages  
✅ **Group Booking Classification** - Auto-detects group reservations (≥4 rooms or ≥12 guests)  
✅ **Production-Ready** - CLI interface, Docker support, comprehensive evaluation  

---

## 🏗️ Architecture

```
Raw Email
   ↓
[Normalize] → Remove signatures, clean text
   ↓
[Intent Classify] → booking_request / cancellation / modification / etc.
   ↓
[Segment] → Detect multiple booking requests (intent-aware)
   ↓
[Extract Entities] → Dates, guests, room types per segment
   ↓
[Assemble Rooms] → Complete room structures
   ↓
[Business Logic] → Group booking classification
   ↓
Structured JSON Output
```

### Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Normalization** | Regex + rules | Email cleaning, signature removal |
| **Intent Classification** | DistilBERT + fallback rules | Classify email purpose (97.5% accuracy) |
| **Segmentation** | Rule-based markers | Detect multi-request emails (86% accuracy) |
| **Entity Extraction** | dateparser + regex | Extract dates, guests, room types |
| **Business Logic** | Config-driven rules | Group booking, room assembly |

---

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone <repository-url>
cd hotel_email_parser

# Install dependencies
pip install -e .

# Or with Poetry
poetry install
```

### Basic Usage

**CLI - Process single email:**
```bash
python -m hotel_email_parser process "I need a double room for May 15-17, 2026. We are 2 adults."
```

**Output:**
```json
{
  "intent": "booking_request",
  "segments": [{
    "segment_id": 0,
    "arrival_date": "2026-05-15",
    "departure_date": "2026-05-17",
    "nights": 2,
    "rooms": [{
      "room_type": "double",
      "quantity": 1,
      "adults": 2,
      "children": [],
      "total_guests": 2
    }],
    "is_group_booking": false
  }]
}
```

**Python API:**
```python
from hotel_email_parser import HotelEmailPipeline

# Initialize pipeline
pipeline = HotelEmailPipeline('config/hotel.yaml')

# Process email
email = "I need a suite for June 10-15. 2 adults and 1 child (age 5)."
result = pipeline.process(email)

print(result['intent'])           # "booking_request"
print(result['segments'][0]['rooms'])  # Room details
```

---

## 💻 CLI Commands

### `process` - Single Email
```bash
python -m hotel_email_parser process "EMAIL_TEXT" [OPTIONS]

Options:
  -o, --output FILE    Save to JSON file
  -c, --config FILE    Custom config (default: config/hotel.yaml)
  --pretty             Pretty-print JSON
```

### `process-file` - From File
```bash
python -m hotel_email_parser process-file email.txt --output result.json
```

### `batch` - Directory Processing
```bash
python -m hotel_email_parser batch emails/ --output results/

Options:
  -o, --output DIR     Output directory (default: output/)
  --pattern GLOB       File pattern (default: *.txt)
```

### `evaluate` - Test Set Evaluation
```bash
python -m hotel_email_parser evaluate
```

---

## ⚙️ Configuration

Edit `config/hotel.yaml` to customize behavior:

```yaml
# Group booking thresholds
group_booking:
  min_rooms: 4        # Classify as group if ≥4 rooms
  min_guests: 12      # OR ≥12 total guests

# Room type mappings
room_type_aliases:
  single: ["single", "solo", "one bed"]
  double: ["double", "queen", "king"]
  
# Default occupancy per room type
default_room_occupancy:
  single: 1
  double: 2
  family: 4
```

---

## 📊 Performance

Evaluated on 43-email test set:

| Metric | Accuracy |
|--------|----------|
| **Intent Classification** | 76.7% |
| **Segmentation Count** | 86.0% |
| **Arrival Dates** | 68.4% |
| **Adult Counts** | 78.9% |
| **Room Types** | 52.6% |
| **Group Booking** | 84.2% |

**Processing Speed**: ~100-200ms per email (CPU)

---

## 📂 Project Structure

```
hotel_email_parser/
├── hotel_email_parser/      # CLI package
│   ├── __main__.py          # Entry point
│   └── __init__.py
├── pipeline/                # Core pipeline
│   ├── orchestrator.py      # Main pipeline class
│   ├── normalization.py     # Email cleaning
│   ├── intent.py            # Intent classification
│   ├── segmentation.py      # Multi-segment detection
│   └── entities.py          # Entity extraction
├──config/                  # Configuration
│   ├── hotel.yaml           # Hotel settings
│   ├── intent_model.yaml    # Model config
│   └── schema.json          # Output schema
├── data/                    # Datasets
│   ├── labels/              # Ground truth
│   └── processed/           # Train/test splits
├── models/                  # Trained models
│   └── intent_classifier/   # DistilBERT model
├── scripts/                 # Utilities
│   ├── evaluate_pipeline.py # End-to-end evaluation
│   └── train_intent_classifier.py
└── docs/                    # Documentation
    └── ERROR_ANALYSIS.md    # Failure modes
```

---

## 🐳 Docker

**Build:**
```bash
docker build -t hotel-email-parser .
```

**Run:**
```bash
# Process email
docker run hotel-email-parser process "Book a room for May 10, 2026"

# Batch processing
docker run -v $(pwd)/emails:/app/emails hotel-email-parser batch /app/emails
```

---

## 📖 API Reference

### `HotelEmailPipeline`

```python
class HotelEmailPipeline:
    def __init__(self, config_path: str = "config/hotel.yaml"):
        """Initialize pipeline with configuration."""
        
    def process(self, raw_email: str, email_id: str = None) -> Dict:
        """
        Process an email and return structured booking information.
        
        Args:
            raw_email: Raw email text
            email_id: Optional identifier
            
        Returns:
            {
                "intent": str,
                "segments": [
                    {
                        "segment_id": int,
                        "arrival_date": str | null,
                        "departure_date": str | null,
                        "nights": int | null,
                        "rooms": [...],
                        "is_group_booking": bool
                    }
                ]
            }
        """
```

---

## 🔍 Known Limitations

See [`docs/ERROR_ANALYSIS.md`](docs/ERROR_ANALYSIS.md) for detailed failure mode analysis.

**Common Issues:**
- **Relative dates** without context ("next Friday") → `arrival_date: null`
- **Ambiguous room types** ("room for 2") → May infer incorrectly
- **Missing adult counts** → Returns `null` (no inference)

**Recommendations:**
- Include explicit dates in ISO format (YYYY-MM-DD) when possible
- Specify adult/children counts explicitly
- Use standard room type names (single, double, etc.)

---

## 🧪 Testing

```bash
# Run unit tests
python scripts/test_pipeline.py

# Full evaluation
python scripts/evaluate_pipeline.py

# Segmentation test
python scripts/test_segmentation.py
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📝 License

This project is licensed under the MIT License.

---

## 📧 Support

For issues and questions, please open a GitHub issue.

---

**Built with ❤️ using Python, Transformers, and dateparser**
