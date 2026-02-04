"""
Entity Extraction Module

Extracts structured entities from email text:
- Dates (arrival, departure, nights)
- Guest counts (adults, children with ages)
- Room types (single, double, twin, suite, etc.)
- Multi-segment detection

Uses a combination of:
- dateparser for date normalization
- Custom regex patterns
- Context-aware extraction
"""

from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date, timedelta
import dateparser
import re
from collections import defaultdict


class EntityExtractor:
    """
    Extract booking-related entities from text using rule-based patterns.
    """
    
    # Date context keywords
    ARRIVAL_KEYWORDS = [
        r'\barriv(?:ing|al|e)\b',
        r'\bcheck[- ]?in\b',
        r'\bfrom\b',
        r'\bstarting\b',
        r'\bbegin(?:ning)?\b'
    ]
    
    DEPARTURE_KEYWORDS = [
        r'\bdepart(?:ing|ure)?\b',
        r'\bcheck[- ]?out\b',
        r'\b(?:un)?til\b',
        r'\bleav(?:ing|e)\b',
        r'\bending\b'
    ]
    
    # Room type patterns
    ROOM_TYPES = {
        'single': [r'\bsingle\b', r'\bone person\b', r'\b1 person\b'],
        'double': [r'\bdouble\b', r'\btwo people\b', r'\b2 people\b'],
        'twin': [r'\btwin\b'],
        'suite': [r'\bsuite\b'],
        'family': [r'\bfamily\b'],
        'king': [r'\bking\b'],
        'queen': [r'\bqueen\b'],
        'deluxe': [r'\bdeluxe\b'],
        'standard': [r'\bstandard\b']
    }
    
    def __init__(self, reference_date: Optional[datetime] = None):
        """
        Args:
            reference_date: Reference for relative dates (defaults to now)
        """
        self.reference_date = reference_date or datetime.now()
    
    def extract(self, text: str) -> Dict[str, Any]:
        """
        Extract all entities from text.
        
        Returns:
            {
                "dates": {...},
                "guests": {...},
                "room_types": [...],
                "segments": [...]  # For multi-segment emails
            }
        """
        # For now, extract as single segment
        # Multi-segment detection will be added later
        
        dates = self._extract_dates(text)
        guests = self._extract_guests(text)
        room_types = self._extract_room_types(text)
        
        return {
            "dates": dates,
            "guests": guests,
            "room_types": room_types
        }
    
    def _extract_dates(self, text: str) -> Dict[str, Any]:
        """
        Extract and normalize dates.
        
        Returns:
        {
            "arrival_date": str | None (ISO 8601),
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
        
        text_lower = text.lower()
        
        # Extract nights first (often most explicit)
        nights = self._extract_nights(text_lower)
        if nights:
            result["nights"] = nights
            result["confidence"]["nights"] = 1.0
        
        # Find date patterns
        date_candidates = self._find_date_candidates(text)
        
        if not date_candidates:
            return result
        
        # Classify dates as arrival/departure based on context
        arrival_dates, departure_dates = self._classify_dates(text, date_candidates)
        
        # Take most confident dates
        if arrival_dates:
            result["arrival_date"] = arrival_dates[0]["date"]
            result["confidence"]["arrival_date"] = arrival_dates[0]["confidence"]
        
        if departure_dates:
            result["departure_date"] = departure_dates[0]["date"]
            result["confidence"]["departure_date"] = departure_dates[0]["confidence"]
        
        # Calculate missing field if we have 2/3
        result = self._fill_missing_date_field(result)
        
        return result
    
    def _extract_nights(self, text: str) -> Optional[int]:
        """Extract number of nights from text."""
        # Pattern: "N nights", "N-night stay", etc.
        patterns = [
            r'(\d+)[- ]nights?',
            r'stay(?:ing)? (?:for )?(\d+) nights?',
            r'(\d+)[- ]night stay'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1))
        
        return None
    
    def _find_date_candidates(self, text: str) -> List[Dict]:
        """
        Find all potential dates in text.
        
        Returns list of:
        {
            "date": ISO date string,
            "raw_text": original text,
            "position": char position in text,
            "parsed_obj": datetime object
        }
        """
        candidates = []
        
        # Pattern 1: ISO dates (YYYY-MM-DD)
        iso_pattern = r'\b(\d{4}-\d{2}-\d{2})\b'
        for match in re.finditer(iso_pattern, text):
            try:
                dt = datetime.strptime(match.group(1), '%Y-%m-%d')
                candidates.append({
                    "date": dt.strftime('%Y-%m-%d'),
                    "raw_text": match.group(0),
                    "position": match.start(),
                    "parsed_obj": dt
                })
            except ValueError:
                continue
        
       # Pattern 2: Month DD, YYYY or Month DD-DD, YYYY
        # Examples: "May 12, 2026", "May 12-15, 2026"
        month_names = r'(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)'
        month_day_pattern = rf'\b({month_names})\s+(\d{{1,2}}(?:-\d{{1,2}})?),?\s+(\d{{4}})\b'
        
        for match in re.finditer(month_day_pattern, text, re.IGNORECASE):
            month_str = match.group(1)
            day_part = match.group(2)
            year_str = match.group(3)
            
            # Handle date ranges like "May 12-15"
            if '-' in day_part:
                days = [int(d) for d in day_part.split('-')]
            else:
                days = [int(day_part)]
            
            for day in days:
                date_str = f"{month_str} {day}, {year_str}"
                parsed = dateparser.parse(date_str)
                if parsed:
                    candidates.append({
                        "date": parsed.strftime('%Y-%m-%d'),
                        "raw_text": match.group(0),
                        "position": match.start(),
                        "parsed_obj": parsed
                    })
        
        # Pattern 2b: "Month DD to Month DD" or "from Month DD to Month DD"
        date_range_pattern = rf'(?:from\s+)?({month_names})\s+(\d{{1,2}})\s+to\s+({month_names})\s+(\d{{1,2}}),?\s*(\d{{4}})?'
        for match in re.finditer(date_range_pattern, text, re.IGNORECASE):
            month1 = match.group(1)
            day1 = match.group(2)
            month2 = match.group(3)
            day2 = match.group(4)
            year = match.group(5) if match.group(5) else datetime.now().year
            
            # Parse both dates
            date1_str = f"{month1} {day1}, {year}"
            date2_str = f"{month2} {day2}, {year}"
            
            for date_str in [date1_str, date2_str]:
                parsed = dateparser.parse(date_str)
                if parsed:
                    iso_date = parsed.strftime('%Y-%m-%d')
                    if not any(c['date'] == iso_date for c in candidates):
                        candidates.append({
                            "date": iso_date,
                            "raw_text": match.group(0),
                            "position": match.start(),
                            "parsed_obj": parsed
                        })
        
        # Pattern 3: DD/MM/YYYY or MM/DD/YYYY
        slash_date_pattern = r'\b(\d{1,2})[/\-](\d{1,2})[/\-](\d{4})\b'
        for match in re.finditer(slash_date_pattern, text):
            date_str = match.group(0)
            parsed = dateparser.parse(date_str, settings={'PREFER_DATES_FROM': 'future'})
            if parsed:
                iso_date = parsed.strftime('%Y-%m-%d')
                # Avoid duplicates
                if not any(c['date'] == iso_date for c in candidates):
                    candidates.append({
                        "date": iso_date,
                        "raw_text": match.group(0),
                        "position": match.start(),
                        "parsed_obj": parsed
                    })
        
        # Pattern 4: Relative dates (tonight, tomorrow, etc.)
        relative_patterns = {
            r'\btonight\b': 0,
            r'\btomorrow\b': 1,
            r'\bnext\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b': 7,  # Approximate
        }
        
        for pattern, days_offset in relative_patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                rel_date = self.reference_date + timedelta(days=days_offset)
                iso_date = rel_date.strftime('%Y-%m-%d')
                if not any(c['date'] == iso_date for c in candidates):
                    candidates.append({
                        "date": iso_date,
                        "raw_text": match.group(0),
                        "position": match.start(),
                        "parsed_obj": rel_date
                    })
        
        # Sort by position in text
        candidates.sort(key=lambda x: x['position'])
        
        return candidates

    
    def _classify_dates(
        self,
        text: str,
        candidates: List[Dict]
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Classify dates as arrival or departure based on context.
        
        Returns: (arrival_dates, departure_dates)
        Each is a list of {"date": str, "confidence": float}
        """
        text_lower = text.lower()
        arrival_dates = []
        departure_dates = []
        
        for candidate in candidates:
            date_str = candidate["date"]
            pos = candidate["position"]
            
            # Get context window around the date (±50 chars)
            start = max(0, pos - 50)
            end = min(len(text), pos + len(candidate["raw_text"]) + 50)
            context = text_lower[start:end]
            
            # Score for arrival context
            arrival_score = sum(
                1 for pattern in self.ARRIVAL_KEYWORDS
                if re.search(pattern, context)
            )
            
            # Score for departure context
            departure_score = sum(
                1 for pattern in self.DEPARTURE_KEYWORDS
                if re.search(pattern, context)
            )
            
            # Classify based on scores
            if arrival_score > departure_score:
                confidence = min(0.9, 0.5 + 0.1 * arrival_score)
                arrival_dates.append({"date": date_str, "confidence": confidence})
            elif departure_score > arrival_score:
                confidence = min(0.9, 0.5 + 0.1 * departure_score)
                departure_dates.append({"date": date_str, "confidence": confidence})
            else:
                # Ambiguous or first date defaults to arrival
                if not arrival_dates:
                    arrival_dates.append({"date": date_str, "confidence": 0.5})
                elif not departure_dates:
                    departure_dates.append({"date": date_str, "confidence": 0.5})
        
        # Sort by confidence
        arrival_dates.sort(key=lambda x: x['confidence'], reverse=True)
        departure_dates.sort(key=lambda x: x['confidence'], reverse=True)
        
        return arrival_dates, departure_dates
    
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
    
    def _extract_guests(self, text: str) -> Dict[str, Any]:
        """
        Extract guest counts.
        
        Returns:
        {
            "adults": int | None,
            "children": [{"age": int}, ...],
            "total_guests": int | None
        }
        """
        text_lower = text.lower()
        
        result = {
            "adults": None,
            "children": [],
            "total_guests": None
        }
        
        # Extract adults
        result["adults"] = self._extract_adult_count(text_lower)
        
        # Extract children with ages
        result["children"] = self._extract_children(text_lower)
        
        # Calculate total if both present
        if result["adults"] is not None:
            total =result["adults"] + len(result["children"])
            result["total_guests"] = total
        
        return result
    
    def _extract_adult_count(self, text: str) -> Optional[int]:
        """Extract number of adults from text."""
        
        # Pattern 1: Explicit "N adults"
        patterns = [
            r'(\d+)\s+adults?',
            r'(\d+)\s+people?',
            r'(\d+)\s+guests?',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        
        # Pattern 2: Solo traveler
        solo_patterns = [
            r'\bjust me\b',
            r'\bsolo\b',
            r'\balone\b',
            r'\b1 person\b',
            r'\bone person\b',
            r'\bsingle occupancy\b'
        ]
        
        for pattern in solo_patterns:
            if re.search(pattern, text):
                return 1
        
        # Pattern 3: "We are N" (implies all adults if no children mentioned)
        we_pattern = r'we are (\d+)'
        match = re.search(we_pattern, text)
        if match:
            # This might include children, handle conservatively
            total = int(match.group(1))
            # Only return if children are mentioned separately
            if 'child' not in text and 'kid' not in text:
                return total
        
        # Pattern 4: DEFAULT - if no explicit count and no children mentioned
        # Assume 1 adult for single room bookings
        if 'child' not in text and 'kid' not in text:
            # Check for booking indicators
            if re.search(r'\b(book|reserve|need|want)\s+(a|one)\s+room\b', text):
                return 1
        
        return None
    
    def _extract_children(self, text: str) -> List[Dict[str, int]]:
        """
        Extract children with ages.
        
        Returns: [{"age": int}, ...]
        """
        children = []
        
        # Pattern 1: "N children (ages X, Y, Z)" or "N kids (X, Y)"
        # Examples: "2 kids (5, 9)", "2 children (ages 5 and 9)"
        children_with_ages_pattern = r'(\d+)\s+(?:children|kids?)\s*\((?:ages?\s*)?([0-9,\s]+)\)'
        match = re.search(children_with_ages_pattern, text)
        
        if match:
            count = int(match.group(1))
            ages_str = match.group(2)
            
            # Parse ages: "5, 9" or "5 and 9"
            ages = []
            for age_match in re.finditer(r'\d+', ages_str):
                ages.append(int(age_match.group()))
            
            # Add children
            for age in ages:
                children.append({"age": age})
            
            # If count != len(ages), add children without ages
            for _ in range(max(0, count - len(ages))):
                children.append({"age": None})
        
        else:
            # Pattern 2: "N children" without ages
            children_no_ages_pattern = r'(\d+)\s+(?:children|kids?)'
            match = re.search(children_no_ages_pattern, text)
            if match:
                count = int(match.group(1))
                for _ in range(count):
                    children.append({"age": None})
            
            # Pattern 3: Individual ages mentioned "child (age 5)"
            individual_age_pattern = r'(?:child|kid).*?\((?:age\s*)?(\d+)\)'
            for match in re.finditer(individual_age_pattern, text):
                age = int(match.group(1))
                children.append({"age": age})
            
            # Pattern 4: "N year old" mentions
            year_old_pattern = r'(\d+)\s*year\s*old'
            for match in re.finditer(year_old_pattern, text):
                age = int(match.group(1))
                # Only count as child if age < 18
                if age < 18:
                    if not any(c.get("age") == age for c in children):
                        children.append({"age": age})
        
        return children

    
    def _extract_room_types(self, text: str) -> List[Dict[str, Any]]:
        """
        Extract room types with quantities.
        
        Returns list of:
        {
            "room_type": str,
            "quantity": int,
            "confidence": float
        }
        """
        text_lower = text.lower()
        rooms = []
        
        # Try to find explicit room type mentions
        for canonical_type, patterns in self.ROOM_TYPES.items():
            for pattern in patterns:
                # Look for quantity before room type
                quantity_pattern = rf'(\d+)\s+{pattern[2:-2]}(?:\s+rooms?)?'
                matches = list(re.finditer(quantity_pattern, text_lower))
                
                if matches:
                    for match in matches:
                        quantity = int(match.group(1))
                        rooms.append({
                            "room_type": canonical_type,
                            "quantity": quantity,
                            "confidence": 0.9
                        })
                else:
                    # Look for room type without explicit quantity
                    if re.search(pattern, text_lower):
                        # Check if already captured with quantity
                        if not any(r['room_type'] == canonical_type for r in rooms):
                            rooms.append({
                                "room_type": canonical_type,
                                "quantity": 1,  # Default to 1
                                "confidence": 0.7
                            })
        
        # If no explicit room type found, try to infer from context
        if not rooms:
            # Look for generic "room" or "a room" patterns
            if re.search(r'\b(a|one)\s+room\b', text_lower):
                # Don't add a room type if we can't determine it
                # This avoids false positives
                pass
        
        return rooms

