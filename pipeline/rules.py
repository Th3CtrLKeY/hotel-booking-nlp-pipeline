"""
Deterministic Rules Engine

Implements rule-based logic for:
- Date conflict resolution (arrival + nights → departure)
- Default occupancy assignment (room type → guest count)
- Data validation and consistency checks
"""

from typing import Dict, Any, Optional, List
from datetime import date, timedelta
import yaml
from pathlib import Path


class RulesEngine:
    """
    Applies deterministic rules to resolve ambiguities and conflicts.
    
    All logic is driven by hotel configuration.
    """
    
    def __init__(self, config_path: Path):
        """
        Args:
            config_path: Path to hotel.yaml configuration
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load hotel configuration."""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def resolve_dates(
        self,
        arrival: Optional[date],
        departure: Optional[date],
        nights: Optional[int]
    ) -> Dict[str, Any]:
        """
        Resolve date conflicts using deterministic rules.
        
        Cases:
        1. arrival + nights → compute departure
        2. arrival + departure → compute nights
        3. departure + nights → compute arrival (rare)
        
        Returns:
            {
                "arrival_date": date,
                "departure_date": date,
                "nights": int,
                "resolution_method": str
            }
        """
        if arrival and nights and not departure:
            # Case 1: arrival + nights
            departure = arrival + timedelta(days=nights)
            return {
                "arrival_date": arrival,
                "departure_date": departure,
                "nights": nights,
                "resolution_method": "arrival_plus_nights"
            }
        
        elif arrival and departure and not nights:
            # Case 2: arrival + departure
            nights = (departure - arrival).days
            return {
                "arrival_date": arrival,
                "departure_date": departure,
                "nights": nights,
                "resolution_method": "date_diff"
            }
        
        elif arrival and departure and nights:
            # All three present: validate consistency
            computed_nights = (departure - arrival).days
            if computed_nights != nights:
                # Conflict: trust dates over nights
                nights = computed_nights
            return {
                "arrival_date": arrival,
                "departure_date": departure,
                "nights": nights,
                "resolution_method": "all_present_validated"
            }
        
        else:
            # Insufficient information
            return {
                "arrival_date": arrival,
                "departure_date": departure,
                "nights": nights,
                "resolution_method": "insufficient_data"
            }
    
    def assign_default_occupancy(self, room_type: str) -> int:
        """
        Get default occupancy for a room type from config.
        
        Args:
            room_type: Canonical room type (e.g., "double")
            
        Returns:
            Default number of guests
        """
        occupancy_map = self.config.get("default_room_occupancy", {})
        return occupancy_map.get(room_type, 1)  # Default to 1 if unknown
    
    def map_room_type(self, raw_room_type: str) -> Optional[str]:
        """
        Map a raw room type to canonical type using config aliases.
        
        Args:
            raw_room_type: Raw text (e.g., "queen bed")
            
        Returns:
            Canonical type (e.g., "double") or None
        """
        aliases = self.config.get("room_type_aliases", {})
        raw_lower = raw_room_type.lower()
        
        for canonical_type, alias_list in aliases.items():
            if any(alias in raw_lower for alias in alias_list):
                return canonical_type
        
        return None
    
    def validate_booking(self, segment: Dict[str, Any]) -> List[str]:
        """
        Validate a booking segment and return errors.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check date logic
        arrival = segment.get("arrival_date")
        departure = segment.get("departure_date")
        
        if arrival and departure:
            if departure <= arrival:
                errors.append("Departure date must be after arrival date")
        
        # Check guest counts
        rooms = segment.get("rooms", [])
        for i, room in enumerate(rooms):
            adults = room.get("adults", 0) or 0
            children_count = len(room.get("children", []))
            total = adults + children_count
            
            if total == 0:
                errors.append(f"Room {i}: No guests specified")
        
        return errors
