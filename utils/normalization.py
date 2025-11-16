import re

def normalize_name(name):
    """
    Normalize the name by:
    - Lowercasing
    - Removing special characters
    - Simplifying featuring artists
    """
    name = name.lower()
    # Remove text within parentheses (including the parentheses)
    name = re.sub(r'\(.*?\)', '', name)
    # Remove special characters
    name = re.sub(r'[^\w\s]', '', name)
    # Simplify "feat." to "ft" or remove it
    name = re.sub(r'\bfeat\b', 'ft', name)
    name = re.sub(r'\bft\b', '', name)
    # Remove extra whitespace
    name = re.sub(r'\s+', ' ', name).strip()
    return name
