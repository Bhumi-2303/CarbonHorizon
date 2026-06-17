import re

# Simple HTML tag stripping
HTML_TAG_RE = re.compile(r'<[^>]*>')

# Common injection vectors
INJECTION_VECTORS = [
    r'ignore all previous instructions',
    r'system override',
    r'you are now',
    r'forget previous instructions',
    r'forget all previous instructions',
    r'disregard previous instructions',
]

def sanitize_text(input_str: str) -> str:
    """
    Sanitizes user input by:
    1. Rejecting script tags.
    2. Rejecting common prompt injection phrases.
    3. Stripping HTML tags.
    4. Rejecting javascript: protocols.
    """
    if not input_str:
        return input_str
        
    # Check for scripts (case insensitive)
    if re.search(r'<script.*?>.*?</script>', input_str, re.IGNORECASE) or '<script' in input_str.lower():
        raise ValueError("Invalid content: scripts are not allowed")

    # Check for prompt injection
    lower_input = input_str.lower()
    for vector in INJECTION_VECTORS:
        if vector in lower_input:
            raise ValueError("Invalid content: malformed payload detected (prompt injection)")

    # Strip HTML tags
    clean_str = HTML_TAG_RE.sub('', input_str)
    
    # Strip any potential markdown script injection (e.g., javascript:alert())
    if 'javascript:' in clean_str.lower():
        raise ValueError("Invalid content: script protocols not allowed")

    return clean_str.strip()
