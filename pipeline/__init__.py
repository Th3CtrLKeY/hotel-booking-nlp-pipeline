"""
Pipeline package for hotel email parsing.

This package contains all pipeline stages:
- normalization: Email cleaning and text normalization
- intent: Intent classification (booking, modification, etc.)
- segmentation: Multi-request detection and splitting
- entities: Entity extraction (dates, guests, room types)
- rules: Deterministic rule engine
- business_logic: Config-driven business rules
"""

__version__ = "0.1.0"
