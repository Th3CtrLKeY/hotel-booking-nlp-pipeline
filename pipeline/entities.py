"""
Entity Extraction Module

Extracts structured entities from email text:
- Dates (arrival, departure, nights)
- Guest counts (adults, children with ages)
- Room types (single, double, twin, suite, etc.)
- Hotel names (if mentioned)

Uses a combination of:
- spaCy NER
- dateparser for date normalization
- Custom regex patterns
- Hotel config for semantic mapping
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, date
import dateparser
import spacy
import re


class EntityExtractor:
    """
    Extract booking-related entities from text.
    
    Combines spaCy's NER with domain-specific rules.
    """
    
    def __init__(
        self,
        spacy_model: str = "en_core_web_sm",
        reference_date: Optional[datetime] = None
    ):
        """
        Args:
            spacy_model: spaCy model name
            reference_date: Reference for relative dates (defaults to now)
        """
        self.spacy_model_name = spacy_model
        self.nlp = None
        self.reference_date = reference_date or datetime.now()
    
    def _load_spacy(self):
        """Lazy load spaCy model."""
        if self.nlp is None:
            self.nlp = spacy.load(self.spacy_model_name)
    
    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract all entities from text.
        
        Returns:
            {
                "dates": [...],
                "guests": {...},
                "room_types": [...],
                "hotel_names": [...]
            }
        """
        self._load_spacy()
        
        # TODO: Implement full extraction in Phase 4
        return {
            "dates": self._extract_dates(text),
            "guests": self._extract_guests(text),
            "room_types": self._extract_room_types(text),
            "hotel_names": self._extract_hotels(text)
        }
    
    def _extract_dates(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract and normalize dates.
        
        Returns list of:
        {
            "raw_text": str,
            "normalized_date": str (ISO 8601),
            "confidence": float,
            "type": "arrival" | "departure" | "unknown"
        }
        """
        # TODO: Implement in Phase 4
        return []
    
    def _extract_guests(self, text: str) -> Dict[str, Any]:
        """
        Extract guest counts.
        
        Returns:
        {
            "adults": int | None,
            "children": [{"age": int}, ...],
            "total": int | None
        }
        """
        # TODO: Implement in Phase 4
        return {"adults": None, "children": [], "total": None}
    
    def _extract_room_types(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract room types with semantic mapping.
        
        Returns list of:
        {
            "raw_text": str,
            "canonical_type": str,
            "confidence": float
        }
        """
        # TODO: Implement in Phase 4
        return []
    
    def _extract_hotels(self, text: str) -> List[str]:
        """Extract hotel names if explicitly mentioned."""
        # TODO: Implement in Phase 4
        return []


def normalize_date(
    date_string: str,
    reference_date: Optional[datetime] = None
) -> Optional[date]:
    """
    Parse and normalize a natural language date.
    
    Args:
        date_string: Natural language date ("next Friday", "May 12")
        reference_date: Reference for relative dates
        
    Returns:
        Normalized date or None if unparseable
    """
    settings = {
        'PREFER_DATES_FROM': 'future',
        'RELATIVE_BASE': reference_date or datetime.now()
    }
    
    parsed = dateparser.parse(date_string, settings=settings)
    return parsed.date() if parsed else None
