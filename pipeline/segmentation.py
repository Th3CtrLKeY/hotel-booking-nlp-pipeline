"""
Email Segmentation Module

Detects and splits multiple booking requests within a single email.

Example:
    "I need a double room July 10-12, and also a suite Aug 5-7"
    → Split into 2 segments for independent processing
"""

from typing import List, Dict, Any
import re


class EmailSegmenter:
    """
    Segments emails containing multiple booking requests.
    
    Uses rule-based markers to detect separate booking requests.
    """
    
    # Explicit segment markers (in order of priority)
    SEGMENT_MARKERS = [
        # Numbered lists
        r'^\s*(\d+)[.)]\s+',  # "1) ...", "1. ...", "2) ..."
        
        # Trip labels
        r'\b(first|second|third)\s+(trip|stay|booking|visit):?',
       
        # Explicit separators
        r'\balso\b[,;:]?\s+',
        r'\badditionally\b[,;:]?\s+',
        r'\bfurthermore\b[,;:]?\s+',
       
        # "Separate" indicators
        r'\bseparate(ly)?\s+(i|we|they)\s+(need|want|require)',
    ]
    
    def __init__(self):
        """Initialize segmenter with default configuration."""
        pass
    
    def segment(self, text: str, intent: str = "booking_request") -> List[Dict[str, Any]]:
        """
        Segment email into individual booking requests.
        
        Args:
            text: Normalized email text
            intent: Email intent (booking_request, cancellation, etc.)
            
        Returns:
            List of segments for booking_request intent.
            Empty list for other intents (no segmentation needed).
            
            Each segment contains:
            - segment_id: int
            - text: str
            - start_char: int
            - end_char: int
            - method: str (detection method used)
        """
        # Only segment booking requests
        if intent != "booking_request":
            return []
        
        # Try rule-based detection
        segments = self._segment_by_rules(text)
        
        # If no segments found, return entire email as single segment
        if not segments:
            segments = [{
                "text": text,
                "start": 0,
                "end": len(text),
                "method": "default"
            }]
        
        # Convert to output format
        return [
            {
                "segment_id": i,
                "text": seg["text"],
                "start_char": seg["start"],
                "end_char": seg["end"],
                "method": seg["method"]
            }
            for i, seg in enumerate(segments)
        ]
    
    def _segment_by_rules(self, text: str) -> List[Dict]:
        """
        Split by explicit segmentation markers.
        
        Returns:
            List of dicts with keys: text, start, end, method
        """
        # Try numbered lists first (highest confidence)
        segments = self._split_by_numbered_lists(text)
        if len(segments) > 1:
            return segments
        
        # Try explicit separators
        segments = self._split_by_separators(text)
        if len(segments) > 1:
            return segments
        
        # Try trip labels
        segments = self._split_by_trip_labels(text)
        if len(segments) > 1:
            return segments
        
        # No segments found
        return []
    
    def _split_by_numbered_lists(self, text: str) -> List[Dict]:
        """
       Detect numbered lists: "1) ...", "2) ...", etc.
        """
        lines = text.split('\n')
        segments = []
        current_segment = []
        current_start = 0
        in_numbered_list = False
        
        for i, line in enumerate(lines):
            # Check if line starts with a number
            match = re.match(r'^\s*(\d+)[.)]\s+', line)
            
            if match:
                # New numbered item
                if current_segment and in_numbered_list:
                    # Save previous segment
                    segment_text = '\n'.join(current_segment)
                    segments.append({
                        "text": segment_text.strip(),
                        "start": current_start,
                        "end": current_start + len(segment_text),
                        "method": "numbered_list"
                    })
                    current_start += len(segment_text) + 1  # +1 for newline
                
                # Start new segment
                current_segment = [line]
                in_numbered_list = True
            else:
                # Continue current segment
                current_segment.append(line)
        
        # Add last segment if we found numbered lists
        if in_numbered_list and current_segment:
            segment_text = '\n'.join(current_segment)
            segments.append({
                "text": segment_text.strip(),
                "start": current_start,
                "end": current_start + len(segment_text),
                "method": "numbered_list"
            })
        
        return segments if len(segments) > 1 else []
    
    def _split_by_separators(self, text: str) -> List[Dict]:
        """
        Split on explicit separators: "Also", "Additionally", "Furthermore".
        
        Must be at start of sentence/paragraph to avoid false positives.
        """
        separator_patterns = [
            r'\n\s*also\b[,;:]?\s+',
            r'\n\s*additionally\b[,;:]?\s+',
            r'\n\s*furthermore\b[,;:]?\s+',
        ]
        
        for pattern in separator_patterns:
            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            if matches:
                segments = []
                last_end = 0
                
                for match in matches:
                    # Add segment before separator
                    if match.start() > last_end:
                        segments.append({
                            "text": text[last_end:match.start()].strip(),
                            "start": last_end,
                            "end": match.start(),
                            "method": "separator"
                        })
                    last_end = match.end()
                
                # Add final segment
                if last_end < len(text):
                    segments.append({
                        "text": text[last_end:].strip(),
                        "start": last_end,
                        "end": len(text),
                        "method": "separator"
                    })
                
                if len(segments) > 1:
                    return segments
        
        return []
    
    def _split_by_trip_labels(self, text: str) -> List[Dict]:
        """
        Split by "First trip", "Second trip", etc.
        """
        pattern = r'\b(first|second|third)\s+(trip|stay|booking|visit):?'
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        
        if len(matches) >= 2:
            segments = []
            
            for i, match in enumerate(matches):
                start = match.start()
                # Find end (next match or end of text)
                end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
                
                segments.append({
                    "text": text[start:end].strip(),
                    "start": start,
                    "end": end,
                    "method": "trip_labels"
                })
            
            return segments
        
        return []
