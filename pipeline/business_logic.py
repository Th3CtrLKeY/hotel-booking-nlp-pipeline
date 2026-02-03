"""
Business Logic Module

Implements hotel-specific business rules:
- Child vs adult classification (age-based)
- Group booking determination
- Special rate logic (future)

All logic is configuration-driven.
"""

from typing import Dict, Any, List
from pathlib import Path
import yaml


class BusinessLogic:
    """
    Applies hotel-specific business rules to booking data.
    
    Configuration-driven: changes to hotel.yaml affect behavior
    without code changes or retraining.
    """
    
    def __init__(self, config_path: Path):
        """
        Args:
            config_path: Path to hotel.yaml
        """
        self.config_path = config_path
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load hotel configuration."""
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)
    
    def classify_guest_age(self, age: int) -> str:
        """
        Classify a guest as child or adult based on age threshold.
        
        Args:
            age: Guest age
            
        Returns:
            "child" or "adult"
        """
        threshold = self.config.get("child_adult_age", 12)
        return "child" if age < threshold else "adult"
    
    def is_group_booking(self, segment: Dict[str, Any]) -> bool:
        """
        Determine if a booking qualifies as a group booking.
        
        Criteria (from config):
        - Number of rooms >= threshold
        - OR total guests >= threshold
        
        Args:
            segment: Booking segment with rooms data
            
        Returns:
            True if group booking
        """
        group_config = self.config.get("group_booking", {})
        room_threshold = group_config.get("room_threshold", 7)
        guest_threshold = group_config.get("guest_threshold", 15)
        
        # Count rooms
        rooms = segment.get("rooms", [])
        num_rooms = len(rooms)
        
        # Count total guests
        total_guests = 0
        for room in rooms:
            adults = room.get("adults", 0) or 0
            children = len(room.get("children", []))
            total_guests += (adults + children)
        
        # Apply criteria
        return num_rooms >= room_threshold or total_guests >= guest_threshold
    
    def enrich_segment(self, segment: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply all business logic to enrich a segment.
        
        Args:
            segment: Raw extracted segment
            
        Returns:
            Enriched segment with business logic applied
        """
        enriched = segment.copy()
        
        # Determine group booking status
        enriched["is_group_booking"] = self.is_group_booking(segment)
        
        # Classify children by age
        for room in enriched.get("rooms", []):
            for child in room.get("children", []):
                if "age" in child:
                    child["classification"] = self.classify_guest_age(child["age"])
        
        return enriched
