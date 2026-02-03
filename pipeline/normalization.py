"""
Email Normalization Module

Cleans and normalizes raw email text for NLP processing.
Removes signatures, disclaimers, excessive whitespace while preserving
span information for provenance tracking.
"""

from typing import Dict, Any, List, Tuple, Optional
import re
import yaml
from pathlib import Path


class EmailNormalizer:
    """
    Normalizes raw email text for NLP processing.
    
    Responsibilities:
    - Remove email signatures (e.g., "Sent from my iPhone")
    - Remove disclaimers and legal text
    - Normalize whitespace (multiple spaces, tabs, newlines)
    - Optionally normalize casing
    - Preserve original text and span mappings for provenance
    
    This is the first stage in the pipeline.
    """
    
    def __init__(
        self,
        config_path: Optional[Path] = None,
        preserve_case: bool = True
    ):
        """
        Args:
            config_path: Path to normalization.yaml config file
            preserve_case: If True, maintains original casing (recommended)
        """
        self.preserve_case = preserve_case
        
        # Load configuration
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "normalization.yaml"
        
        self.config = self._load_config(config_path)
        
        # Compile regex patterns
        self.signature_patterns = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL)
            for pattern in self.config.get("signature_patterns", [])
        ]
        
        self.disclaimer_patterns = [
            re.compile(pattern, re.IGNORECASE | re.DOTALL)
            for pattern in self.config.get("disclaimer_patterns", [])
        ]
        
        self.greeting_patterns = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.config.get("greeting_patterns", [])
        ]
        
        self.options = self.config.get("options", {})
        self.whitespace_config = self.config.get("whitespace", {})
    
    def _load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load normalization configuration from YAML."""
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            # Return default config if file not found
            return {
                "signature_patterns": [],
                "disclaimer_patterns": [],
                "greeting_patterns": [],
                "options": {
                    "remove_signatures": True,
                    "remove_disclaimers": True,
                    "remove_greetings": False,
                    "normalize_whitespace": True
                },
                "whitespace": {
                    "max_consecutive_newlines": 2,
                    "tab_to_spaces": 4
                }
            }
    
    def normalize(self, raw_email: str) -> Dict[str, Any]:
        """
        Normalize a raw email string.
        
        Args:
            raw_email: Raw email content (body only, no headers)
            
        Returns:
            Dictionary containing:
            - normalized_text: Cleaned text
            - original_text: Original text
            - spans_removed: List of (start, end, reason) tuples
            - metadata: Normalization statistics
        """
        if not raw_email:
            return {
                "normalized_text": "",
                "original_text": "",
                "spans_removed": [],
                "metadata": {
                    "chars_removed": 0,
                    "normalization_applied": []
                }
            }
        
        text = raw_email
        spans_removed = []
        normalization_applied = []
        
        # Remove signatures
        if self.options.get("remove_signatures", True):
            text, sig_spans = remove_signatures(text, self.signature_patterns)
            spans_removed.extend(sig_spans)
            if sig_spans:
                normalization_applied.append("signature_removal")
        
        # Remove disclaimers
        if self.options.get("remove_disclaimers", True):
            text, disc_spans = remove_disclaimers(text, self.disclaimer_patterns)
            spans_removed.extend(disc_spans)
            if disc_spans:
                normalization_applied.append("disclaimer_removal")
        
        # Remove greetings (optional)
        if self.options.get("remove_greetings", False):
            text, greet_spans = remove_greetings(text, self.greeting_patterns)
            spans_removed.extend(greet_spans)
            if greet_spans:
                normalization_applied.append("greeting_removal")
        
        # Normalize whitespace
        if self.options.get("normalize_whitespace", True):
            text = normalize_whitespace(
                text,
                max_newlines=self.whitespace_config.get("max_consecutive_newlines", 2),
                tab_to_spaces=self.whitespace_config.get("tab_to_spaces", 4)
            )
            normalization_applied.append("whitespace_normalization")
        
        # Final trim
        text = text.strip()
        
        return {
            "normalized_text": text,
            "original_text": raw_email,
            "spans_removed": spans_removed,
            "metadata": {
                "chars_removed": len(raw_email) - len(text),
                "normalization_applied": normalization_applied,
                "original_length": len(raw_email),
                "normalized_length": len(text)
            }
        }


def remove_signatures(text: str, patterns: List[re.Pattern]) -> Tuple[str, List[Tuple[int, int, str]]]:
    """
    Remove common email signatures.
    
    Args:
        text: Email text
        patterns: Compiled regex patterns for signatures
        
    Returns:
        (cleaned_text, removed_spans)
    """
    spans_removed = []
    
    for pattern in patterns:
        matches = list(pattern.finditer(text))
        # Process matches in reverse to maintain indices
        for match in reversed(matches):
            start, end = match.span()
            spans_removed.append((start, end, "signature"))
            text = text[:start] + text[end:]
    
    return text, spans_removed


def remove_disclaimers(text: str, patterns: List[re.Pattern]) -> Tuple[str, List[Tuple[int, int, str]]]:
    """
    Remove legal disclaimers and confidentiality notices.
    
    Args:
        text: Email text
        patterns: Compiled regex patterns for disclaimers
        
    Returns:
        (cleaned_text, removed_spans)
    """
    spans_removed = []
    
    for pattern in patterns:
        matches = list(pattern.finditer(text))
        # Process matches in reverse to maintain indices
        for match in reversed(matches):
            start, end = match.span()
            spans_removed.append((start, end, "disclaimer"))
            text = text[:start] + text[end:]
    
    return text, spans_removed


def remove_greetings(text: str, patterns: List[re.Pattern]) -> Tuple[str, List[Tuple[int, int, str]]]:
    """
    Remove email greetings (optional, less aggressive).
    
    Args:
        text: Email text
        patterns: Compiled regex patterns for greetings
        
    Returns:
        (cleaned_text, removed_spans)
    """
    spans_removed = []
    
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            start, end = match.span()
            spans_removed.append((start, end, "greeting"))
            text = text[end:]
            break  # Only remove first greeting
    
    return text, spans_removed


def normalize_whitespace(
    text: str,
    max_newlines: int = 2,
    tab_to_spaces: int = 4
) -> str:
    """
    Normalize excessive whitespace while preserving paragraph structure.
    
    Args:
        text: Text to normalize
        max_newlines: Maximum consecutive newlines to keep
        tab_to_spaces: Number of spaces to replace tabs with
        
    Returns:
        Normalized text
    """
    # Replace tabs with spaces
    text = text.replace('\t', ' ' * tab_to_spaces)
    
    # Collapse multiple spaces to single space (except newlines)
    text = re.sub(r'[^\S\n]+', ' ', text)
    
    # Collapse excessive newlines
    text = re.sub(r'\n{' + str(max_newlines + 1) + r',}', '\n' * max_newlines, text)
    
    # Remove leading/trailing whitespace from each line
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    text = '\n'.join(lines)
    
    return text
