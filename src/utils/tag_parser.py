"""Utility functions for parsing and validating tags."""
import json
from typing import Union, List, Optional
import logging

logger = logging.getLogger(__name__)


def parse_tags_input(value: Union[List[str], str, None]) -> Optional[List[str]]:
    """
    Parse tags input that can be in various formats:
    - Already a list: ["tag1", "tag2"]
    - JSON string: '["tag1", "tag2"]'
    - Comma-separated string: "tag1, tag2"
    - Single tag string: "tag"
    - None or empty
    
    Returns:
        List of parsed tags or None if no valid tags found
    """
    try:
        if value is None:
            return None
        
        if isinstance(value, list):
            # Already a list, just validate and clean
            tags = [str(tag).strip() for tag in value if str(tag).strip()]
            return tags if tags else None
        
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return None
                
            # Try to parse as JSON first
            if value.startswith('[') and value.endswith(']'):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        tags = [str(tag).strip() for tag in parsed if str(tag).strip()]
                        return tags if tags else None
                except (json.JSONDecodeError, ValueError):
                    # If JSON parsing fails, continue with other methods
                    pass
            
            # Try comma-separated
            if ',' in value:
                tags = [tag.strip() for tag in value.split(',') if tag.strip()]
                return tags if tags else None
            
            # Treat as single tag
            return [value]
        
        # For any other type, try to convert to string
        try:
            converted = str(value).strip()
            return [converted] if converted else None
        except Exception:
            logger.warning(f"Failed to convert tags value to string: {value}")
            return None
            
    except Exception as e:
        logger.error(f"Error parsing tags: {e}. Input was: {value}")
        return None