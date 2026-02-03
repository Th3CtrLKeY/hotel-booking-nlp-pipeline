"""
Configuration Management

Utilities for loading and validating hotel configuration.
"""

from typing import Dict, Any
from pathlib import Path
import yaml
import json


def load_hotel_config(config_path: Path) -> Dict[str, Any]:
    """
    Load and validate hotel configuration from YAML file.
    
    Args:
        config_path: Path to hotel.yaml
        
    Returns:
        Configuration dictionary
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config is invalid
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Hotel config not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Validate required fields
    required_fields = [
        "hotel_id",
        "child_adult_age",
        "default_room_occupancy",
        "group_booking"
    ]
    
    for field in required_fields:
        if field not in config:
            raise ValueError(f"Missing required config field: {field}")
    
    return config


def load_json_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load JSON schema for output validation.
    
    Args:
        schema_path: Path to schema.json
        
    Returns:
        JSON schema dictionary
    """
    with open(schema_path, 'r') as f:
        return json.load(f)


def validate_output_against_schema(output: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate output JSON against schema.
    
    Args:
        output: Parsed output
        schema: JSON schema
        
    Returns:
        True if valid
        
    Note:
        For full validation, use jsonschema library.
        This is a basic check for required fields.
    """
    # Basic validation
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in output:
            return False
    
    # Check intent enum
    valid_intents = schema["properties"]["intent"]["enum"]
    if output.get("intent") not in valid_intents:
        return False
    
    return True
