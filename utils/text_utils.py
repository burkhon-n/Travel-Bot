"""Utility functions for text formatting."""


def format_name(name: str) -> str:
    """Format a name with proper capitalization.
    
    Every word starts with a capital letter, rest are lowercase.
    Handles multiple spaces and special characters.
    
    Args:
        name: Raw name string from user input
        
    Returns:
        Formatted name with proper capitalization
        
    Examples:
        >>> format_name("JOHN DOE")
        'John Doe'
        >>> format_name("mary jane smith")
        'Mary Jane Smith'
        >>> format_name("o'BRIEN")
        "O'Brien"
        >>> format_name("jean-CLAUDE")
        'Jean-Claude'
    """
    if not name:
        return ""
    
    # Split by spaces and format each word
    words = name.strip().split()
    formatted_words = []
    
    for word in words:
        if not word:
            continue
            
        # Handle hyphenated names (e.g., Jean-Claude)
        if '-' in word:
            parts = word.split('-')
            formatted_parts = [part.capitalize() for part in parts if part]
            formatted_words.append('-'.join(formatted_parts))
        
        # Handle apostrophes (e.g., O'Brien, D'Angelo)
        elif "'" in word:
            parts = word.split("'")
            formatted_parts = [part.capitalize() for part in parts if part]
            formatted_words.append("'".join(formatted_parts))
        
        else:
            # Standard capitalization
            formatted_words.append(word.capitalize())
    
    return ' '.join(formatted_words)


def format_full_name(first_name: str, last_name: str) -> tuple[str, str]:
    """Format both first and last names.
    
    Args:
        first_name: Raw first name
        last_name: Raw last name
        
    Returns:
        Tuple of (formatted_first_name, formatted_last_name)
    """
    return format_name(first_name), format_name(last_name)
