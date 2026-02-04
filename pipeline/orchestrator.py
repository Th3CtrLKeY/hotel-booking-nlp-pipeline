"""
Pipeline Orchestrator - End-to-End Email Processing

Integrates all pipeline components:
- Normalization
- Intent Classification  
- Segmentation
- Entity Extraction
- Room Assembly
- Business Logic (group booking classification)
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

from pipeline.normalization import EmailNormalizer
from pipeline.intent import IntentClassifier
from pipeline.segmentation import EmailSegmenter
from pipeline.entities import EntityExtractor


class HotelEmailPipeline:
    """
    End-to-end pipeline for processing hotel booking emails.
    
    Usage:
        pipeline = HotelEmailPipeline('config/hotel.yaml')
        result = pipeline.process(raw_email_text)
    """
    
    def __init__(self, config_path: str = "config/hotel.yaml"):
        """
        Initialize pipeline with all components.
        
        Args:
            config_path: Path to hotel configuration YAML
        """
        # Load configuration
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # Initialize components
        self.normalizer = EmailNormalizer()
        self.intent_classifier = IntentClassifier()
        self.segmenter = EmailSegmenter()
        self.entity_extractor = EntityExtractor()
        
        # Group booking thresholds
        self.group_min_rooms = self.config.get('group_booking', {}).get('min_rooms', 7)
        self.group_min_guests = self.config.get('group_booking', {}).get('min_guests', 15)
    
    def process(self, raw_email: str, email_id: str = None) -> Dict[str, Any]:
        """
        Process a raw email through the full pipeline.
        
        Args:
            raw_email: Raw email text
            email_id: Optional email identifier
            
        Returns:
            Structured booking information matching schema.json
        """
        # Step 1: Normalize email
        normalized = self.normalizer.normalize(raw_email)
        clean_text = normalized['normalized_text']
        
        # Step 2: Classify intent
        intent_result = self.intent_classifier.classify(clean_text)
        intent = intent_result['intent']
        
        # Step 3: Segment email (intent-aware)
        segments_raw = self.segmenter.segment(clean_text, intent=intent)
        
        # Step 4: Process each segment
        segments = []
        for segment_data in segments_raw:
            # Extract entities
            entities = self.entity_extractor.extract(segment_data['text'])
            
            # Assemble rooms
            rooms = self._assemble_rooms(entities)
            
            # Classify group booking
            is_group = self._is_group_booking(rooms)
            
            # Build segment result
            segments.append({
                "segment_id": segment_data['segment_id'],
                "arrival_date": entities['dates'].get('arrival_date'),
                "departure_date": entities['dates'].get('departure_date'),
                "nights": entities['dates'].get('nights'),
                "rooms": rooms,
                "is_group_booking": is_group
            })
        
        # Step 5: Build final output
        result = {
            "intent": intent,
            "segments": segments
        }
        
        if email_id:
            result["email_id"] = email_id
        
        return result
    
    def _assemble_rooms(self, entities: Dict) -> List[Dict]:
        """
        Assemble complete room structures from extracted entities.
        
        Strategy:
        - Use null for missing data (no inference)
        - Combine room_type + guests into structured rooms
        - Calculate total_guests for each room
        
        Args:
            entities: Extracted entities (dates, guests, room_types)
            
        Returns:
            List of room objects with structure:
            {
                "room_type": str,
                "quantity": int,
                "adults": int or null,
                "children": list,
                "total_guests": int or null
            }
        """
        room_types = entities.get('room_types', [])
        guests = entities.get('guests', {})
        
        adults = guests.get('adults')
        children = guests.get('children', [])
        
        # If no room types extracted, return empty list (null behavior)
        if not room_types:
            # Still create a room entry if we have guest data
            if adults is not None or children:
                return [{
                    "room_type": None,  # Unknown room type
                    "quantity": 1,
                    "adults": adults,
                    "children": children,
                    "total_guests": self._calculate_total_guests(adults, children)
                }]
            return []
        
        # Assemble rooms from extracted types
        rooms = []
        for room_type_data in room_types:
            room = {
                "room_type": room_type_data.get('room_type'),
                "quantity": room_type_data.get('quantity', 1),
                "adults": adults,
                "children": children,
                "total_guests": self._calculate_total_guests(adults, children)
            }
            rooms.append(room)
        
        return rooms
    
    def _calculate_total_guests(
        self, 
        adults: Optional[int], 
        children: List[Dict]
    ) -> Optional[int]:
        """
        Calculate total guests from adults + children.
        
        Returns null if adults is null.
        """
        if adults is None:
            return None
        return adults + len(children)
    
    def _is_group_booking(self, rooms: List[Dict]) -> bool:
        """
        Classify booking as group based on configuration thresholds.
        
        Rules:
        - Group if total_rooms >= min_rooms (default 4)
        - OR total_guests >= min_guests (default 12)
        
        Args:
            rooms: List of room objects
            
        Returns:
            True if group booking, False otherwise
        """
        if not rooms:
            return False
        
        # Calculate totals
        total_rooms = sum(r.get('quantity', 1) for r in rooms)
        
        # Calculate total guests (handle None values)
        total_guests = 0
        for room in rooms:
            if room.get('total_guests') is not None:
                total_guests += room['total_guests'] * room.get('quantity', 1)
        
        # Apply thresholds
        return (
            total_rooms >= self.group_min_rooms or
            (total_guests > 0 and total_guests >= self.group_min_guests)
        )
