"""
Text processing utilities for Door Installation Assistant
"""

import re
import string
from typing import List, Dict, Any, Set, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Common stopwords for filtering
STOPWORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
    'which', 'this', 'that', 'these', 'those', 'then', 'just', 'so', 'than',
    'such', 'both', 'through', 'about', 'for', 'is', 'of', 'while', 'during',
    'to', 'from', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further',
    'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any',
    'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
    'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'can', 'will',
    'just', 'should', 'now', 'am', 'are', 'was', 'were', 'been', 'being', 'have',
    'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'would', 'could', 'should',
    'shall', 'might', 'must'
}

# Domain-specific keywords that should be preserved
DOOR_KEYWORDS = {
    'door', 'installation', 'interior', 'exterior', 'prehung', 'bifold',
    'knob', 'handle', 'hinge', 'jamb', 'frame', 'trim', 'threshold',
    'shim', 'level', 'plumb', 'square', 'drill', 'screw', 'nail',
    'hammer', 'measure', 'cut', 'fit', 'adjust', 'gap', 'space',
    'clearance', 'swing', 'open', 'close', 'latch', 'lock', 'strike',
    'plate', 'mortise', 'bore', 'hole', 'hardware', 'tool', 'component',
    'entry', 'patio', 'dentil', 'shelf', 'instructions'
}

def extract_keywords(text: str, include_door_terms: bool = True) -> List[str]:
    """
    Extract keywords from text, removing stopwords.
    
    Args:
        text: Text to extract keywords from
        include_door_terms: Whether to include domain-specific door terms
        
    Returns:
        List of keywords
    """
    # Convert to lowercase and remove punctuation
    text = text.lower()
    text = re.sub(f'[{re.escape(string.punctuation)}]', ' ', text)
    
    # Split into words
    words = text.split()
    
    # Remove stopwords and short words
    keywords = [word for word in words if word not in STOPWORDS and len(word) > 2]
    
    # Add back domain-specific keywords if requested
    if include_door_terms:
        door_terms = [word for word in words if word in DOOR_KEYWORDS]
        for term in door_terms:
            if term not in keywords:
                keywords.append(term)
    
    return keywords

def normalize_text(text: str) -> str:
    """
    Normalize text for consistent comparison.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove punctuation
    text = re.sub(f'[{re.escape(string.punctuation)}]', ' ', text)
    
    # Normalize whitespace again
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def extract_sentences(text: str) -> List[str]:
    """
    Extract sentences from text.
    
    Args:
        text: Text to extract sentences from
        
    Returns:
        List of sentences
    """
    # Simple sentence splitting on common sentence terminators
    # This is a basic implementation and may not work perfectly for all cases
    sentence_terminators = ['. ', '! ', '? ', '.\n', '!\n', '?\n']
    
    sentences = []
    current_sentence = text
    
    for terminator in sentence_terminators:
        sentence_parts = []
        for part in current_sentence.split(terminator):
            if part:
                sentence_parts.append(part)
        
        if len(sentence_parts) > 1:
            for i, part in enumerate(sentence_parts[:-1]):
                sentences.append(part + terminator[0])
            current_sentence = sentence_parts[-1]
        else:
            current_sentence = sentence_parts[0] if sentence_parts else ""
    
    if current_sentence:
        sentences.append(current_sentence)
    
    return sentences

def identify_door_type(text: str) -> Tuple[str, str]:
    """
    Identify door category and type from text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Tuple of (door_category, door_type)
    """
    text_lower = text.lower()
    
    # Initialize with unknown values
    door_category = "unknown"
    door_type = "unknown"
    
    # Check for door categories
    if "interior" in text_lower:
        door_category = "interior"
    elif "exterior" in text_lower:
        door_category = "exterior"
    
    # Check for interior door types
    if "bifold" in text_lower:
        door_type = "bifold"
        door_category = "interior"  # Bifold is always interior
    elif "prehung" in text_lower and "interior" in text_lower:
        door_type = "prehung"
        door_category = "interior"
    
    # Check for exterior door types
    elif "entry" in text_lower or "front" in text_lower:
        door_type = "entry door"
        door_category = "exterior"  # Entry is always exterior
    elif "patio" in text_lower or "sliding" in text_lower:
        door_type = "patio door"
        door_category = "exterior"  # Patio is always exterior
    elif "dentil" in text_lower or "shelf" in text_lower:
        door_type = "dentil shelf"
        door_category = "exterior"  # Dentil shelf is always exterior
    elif "prehung" in text_lower and "exterior" in text_lower:
        door_type = "entry door"
        door_category = "exterior"
    
    return door_category, door_type

def extract_step_number(text: str) -> Optional[int]:
    """
    Extract step number from text.
    
    Args:
        text: Text to extract step number from
        
    Returns:
        Step number if found, None otherwise
    """
    # Look for step number patterns
    step_patterns = [
        r'step\s+(\d+)',      # "Step 1"
        r'(\d+)\.\s+',        # "1. "
        r'(\d+)\)\s+',        # "1) "
    ]
    
    for pattern in step_patterns:
        match = re.search(pattern, text.lower())
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
    
    return None

def extract_tools(text: str) -> List[str]:
    """
    Extract tool names from text.
    
    Args:
        text: Text to extract tools from
        
    Returns:
        List of tool names
    """
    tool_patterns = [
        r'hammer', r'screwdriver', r'drill', r'saw', r'level', r'square',
        r'tape measure', r'pencil', r'utility knife', r'chisel', r'pliers',
        r'wrench', r'nail set', r'pry bar', r'caulk gun', r'scissors',
        r'staple gun', r'clamp'
    ]
    
    found_tools = []
    text_lower = text.lower()
    
    for pattern in tool_patterns:
        if re.search(rf'\b{pattern}\b', text_lower):
            found_tools.append(pattern)
    
    return found_tools

def extract_measurements(text: str) -> List[Dict[str, Any]]:
    """
    Extract measurements from text.
    
    Args:
        text: Text to extract measurements from
        
    Returns:
        List of dictionaries with measurement information
    """
    # Pattern to match common measurement formats
    measurement_pattern = r'(\d+(?:\.\d+)?)\s*(inch(?:es)?|in\.|in|ft\.|ft|foot|feet|mm|cm|m|"|\')'
    
    measurements = []
    for match in re.finditer(measurement_pattern, text, re.IGNORECASE):
        value_str, unit = match.groups()
        
        try:
            value = float(value_str)
            
            # Normalize unit
            if unit in ['"', 'inch', 'inches', 'in.', 'in']:
                unit = 'inches'
            elif unit in ["'", 'ft.', 'ft', 'foot', 'feet']:
                unit = 'feet'
            
            measurements.append({
                'value': value,
                'unit': unit,
                'text': match.group(0)
            })
        except ValueError:
            pass
    
    return measurements

def calculate_text_similarity(text1: str, text2: str) -> float:
    """
    Calculate text similarity using basic approach.
    
    Args:
        text1: First text
        text2: Second text
        
    Returns:
        Similarity score between 0 and 1
    """
    # Normalize texts
    text1_norm = normalize_text(text1)
    text2_norm = normalize_text(text2)
    
    # Extract words
    words1 = set(text1_norm.split())
    words2 = set(text2_norm.split())
    
    # Calculate Jaccard similarity
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)