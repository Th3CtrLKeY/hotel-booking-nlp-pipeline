"""
GLiNER-based Entity Extractor

Uses GLiNER for zero-shot named entity recognition with booking-specific labels.
Combines ML-based extraction with rule-based post-processing for robustness.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import dateparser
import re

try:
    from gliner import GLiNER
    GLINER_AVAILABLE = True
except ImportError:
    GLINER_AVAILABLE = False
    print("Warning: GLiNER not available. Install with: pip install gliner")


class GLiNEREntityExtractor:
    """
    Extract booking entities using GLiNER zero-shot NER.
    """
    
    # Custom entity labels for hotel bookings
    ENTITY_LABELS = [
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
    
    def __init__(
        self,
        model_name: str = "urchade/gliner_medium-v2.1",
        threshold: float = 0.4,
        reference_date: Optional[datetime] = None
    ):
        """
        Args:
            model_name: HuggingFace model identifier
            threshold: Confidence threshold for entity extraction
            reference_date: Reference for relative dates (defaults to now)
        """
        if not GLINER_AVAILABLE:
            raise ImportError("GLiNER not installed. Run: pip install gliner")
        
        print(f"Loading GLiNER model: {model_name}...")
        self.model = GLiNER.from_pretrained(model_name)
        self.threshold = threshold
        self.reference_date = reference_date or datetime.now()
        print("GLiNER model loaded successfully!")
    
    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract all entities from text using GLiNER + rules.
        
        Returns:
            {
                "dates": {...},
                "guests": {...},
                "room_types": [...]
            }
        """
        # 1. Extract entities with GLiNER
        entities = self.model.predict_entities(
            text,
            self.ENTITY_LABELS,
            threshold=self.threshold
        )
        
        # 2. Group entities by category
        grouped = self._group_entities(entities)
        
        # 3. Process and normalize
        dates = self._process_dates(grouped, text)
        guests = self._process_guests(grouped, text)
        room_types = self._process_room_types(grouped)
        
        return {
            "dates": dates,
            "guests": guests,
            "room_types": room_types,
            "raw_entities": entities  # For debugging
        }
    
    def _group_entities(self, entities: List[Dict]) -> Dict[str, List[str]]:
        """Group entities by label."""
        grouped = {}
        for entity in entities:
            label = entity['label']
            text = entity['text']
            
            if label not in grouped:
                grouped[label] = []
            grouped[label].append(text)
        
        return grouped
    
    def _process_dates(self, grouped: Dict, full_text: str) -> Dict[str, Any]:
        """
       Process date entities into structured format.
        
        Returns:
        {
            "arrival_date": str | None,
            "departure_date": str | None,
            "nights": int | None,
            "confidence": {...}
        }
        """
        result = {
            "arrival_date": None,
            "departure_date": None,
            "nights": None,
            "confidence": {
                "arrival_date": 0.0,
                "departure_date": 0.0,
                "nights": 0.0
            }
        }
        
        # Extract arrival date
        arrival_candidates = (
            grouped.get("arrival date", []) + 
            grouped.get("check-in date", [])
        )
        if arrival_candidates:
            result["arrival_date"] = self._normalize_date(arrival_candidates[0])
            result["confidence"]["arrival_date"] = 0.8 if result["arrival_date"] else 0.0
        
        # Extract departure date
        departure_candidates = (
            grouped.get("departure date", []) +
            grouped.get("check-out date", [])
        )
        if departure_candidates:
            result["departure_date"] = self._normalize_date(departure_candidates[0])
            result["confidence"]["departure_date"] = 0.8 if result["departure_date"] else 0.0
        
        # Extract nights
        nights_candidates = grouped.get("number of nights", [])
        if nights_candidates:
            result["nights"] = self._extract_number(nights_candidates[0])
            result["confidence"]["nights"] = 1.0 if result["nights"] else 0.0
        
        # Calculate missing field if we have 2/3
        result = self._fill_missing_date_field(result)
        
        return result
    
    def _process_guests(self, grouped: Dict, full_text: str) -> Dict[str, Any]:
        """
        Process guest entities.
        
        Returns:
        {
            "adults": int | None,
            "children": [{"age": int}, ...],
            "total_guests": int | None
        }
        """
        result = {
            "adults": None,
            "children": [],
            "total_guests": None
        }
        
        # Extract adults
        adult_candidates = (
            grouped.get("number of adults", []) +
            grouped.get("number of guests", [])
        )
        if adult_candidates:
            result["adults"] = self._extract_number(adult_candidates[0])
        
        # Default to 1 adult if not found (common implicit case)
        if result["adults"] is None:
            # Check for solo indicators
            if re.search(r'\b(just me|solo|alone)\b', full_text.lower()):
                result["adults"] = 1
        
        # Extract children
        children_candidates = grouped.get("number of children", [])
        child_age_candidates = grouped.get("child age", [])
        
        if children_candidates:
            num_children = self._extract_number(children_candidates[0])
            if num_children:
                # Add children without ages
                result["children"] = [{"age": None} for _ in range(num_children)]
        
        # Add ages if found
        for age_text in child_age_candidates:
            age = self._extract_number(age_text)
            if age and age < 18:  # Sanity check
                # Try to match with existing children or add new
                if result["children"]:
                    # Replace first None age
                    for child in result["children"]:
                        if child["age"] is None:
                            child["age"] = age
                            break
                else:
                    result["children"].append({"age": age})
        
        # Calculate total
        if result["adults"] is not None:
            result["total_guests"] = result["adults"] + len(result["children"])
        
        return result
    
    def _process_room_types(self, grouped: Dict) -> List[Dict[str, Any]]:
        """
        Process room type entities.
        
        Returns: [{"room_type": str, "quantity": int, "confidence": float}]
        """
        room_candidates = grouped.get("room type", [])
        
        rooms = []
        for room_text in room_candidates:
            # Normalize room type
            room_type = self._normalize_room_type(room_text)
            
            # Try to extract quantity
            quantity_match = re.search(r'(\d+)', room_text)
            quantity = int(quantity_match.group(1)) if quantity_match else 1
            
            rooms.append({
                "room_type": room_type,
                "quantity": quantity,
                "confidence": 0.8
            })
        
        return rooms
    
    def _normalize_date(self, date_text: str) -> Optional[str]:
        """Parse and normalize a date string to ISO format."""
        if not date_text:
            return None
        
        parsed = dateparser.parse(
            date_text,
            settings={
                'PREFER_DATES_FROM': 'future',
                'RELATIVE_BASE': self.reference_date
            }
        )
        
        return parsed.strftime('%Y-%m-%d') if parsed else None
    
    def _extract_number(self, text: str) -> Optional[int]:
        """Extract integer from text."""
        if not text:
            return None
        
        match = re.search(r'\d+', text)
        return int(match.group()) if match else None
    
    def _normalize_room_type(self, room_text: str) -> str:
        """Normalize room type to canonical form."""
        room_text_lower = room_text.lower()
        
        # Mapping to canonical types
        if 'single' in room_text_lower:
            return 'single'
        elif 'double' in room_text_lower:
            return 'double'
        elif 'twin' in room_text_lower:
            return 'twin'
        elif 'suite' in room_text_lower:
            return 'suite'
        elif 'family' in room_text_lower:
            return 'family'
        elif 'king' in room_text_lower:
            return 'king'
        elif 'queen' in room_text_lower:
            return 'queen'
        elif 'deluxe' in room_text_lower:
            return 'deluxe'
        else:
            return room_text_lower  # Return as-is if unknown
    
    def _fill_missing_date_field(self, result: Dict) -> Dict:
        """
        Calculate missing date field if we have 2 out of 3.
        
        arrival + nights → departure
        departure + nights → arrival
        arrival + departure → nights
        """
        arrival = result.get("arrival_date")
        departure = result.get("departure_date")
        nights = result.get("nights")
        
        if arrival and departure and not nights:
            # Calculate nights
            arr_date = datetime.strptime(arrival, '%Y-%m-%d')
            dep_date = datetime.strptime(departure, '%Y-%m-%d')
            nights_calc = (dep_date - arr_date).days
            if nights_calc > 0:
                result["nights"] = nights_calc
                result["confidence"]["nights"] = 0.9
        
        elif arrival and nights and not departure:
            # Calculate departure
            arr_date = datetime.strptime(arrival, '%Y-%m-%d')
            dep_date = arr_date + timedelta(days=nights)
            result["departure_date"] = dep_date.strftime('%Y-%m-%d')
            result["confidence"]["departure_date"] = 0.8
        
        elif departure and nights and not arrival:
            # Calculate arrival
            dep_date = datetime.strptime(departure, '%Y-%m-%d')
            arr_date = dep_date - timedelta(days=nights)
            result["arrival_date"] = arr_date.strftime('%Y-%m-%d')
            result["confidence"]["arrival_date"] = 0.8
        
        return result
