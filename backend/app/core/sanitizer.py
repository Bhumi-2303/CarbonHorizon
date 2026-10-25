"""
HTML and text sanitization module using allowlist-based sanitization (nh3).
Provides defense-in-depth against XSS, script injection, and prompt injection.
"""
import re
import nh3

# Safe allowlist for rich text / markdown output (coach responses)
ALLOWED_TAGS = {
    "a", "abbr", "b", "blockquote", "code", "em", "h1", "h2", "h3",
    "h4", "h5", "h6", "hr", "i", "li", "ol", "p", "pre", "strong", "ul"
}

ALLOWED_ATTRIBUTES = {
    "a": {"href", "title", "target"}
}

ALLOWED_URL_SCHEMES = {"http", "https", "mailto"}

# Common injection vectors
INJECTION_VECTORS = [
    r"ignore all previous instructions",
    r"system override",
    r"you are now",
    r"forget previous instructions",
    r"forget all previous instructions",
    r"disregard previous instructions",
]


def sanitize_text(input_str: str) -> str:
    """
    Sanitizes user input by:
    1. Rejecting script tags.
    2. Rejecting common prompt injection phrases.
    3. Stripping all HTML tags using nh3 allowlist.
    4. Rejecting javascript: protocols.
    """
    if not input_str:
        return input_str

    # Check for scripts (case insensitive)
    if (
        re.search(r"<script.*?>.*?</script>", input_str, re.IGNORECASE)
        or "<script" in input_str.lower()
    ):
        raise ValueError("Invalid content: scripts are not allowed")

    # Check for prompt injection
    lower_input = input_str.lower()
    for vector in INJECTION_VECTORS:
        if vector in lower_input:
            raise ValueError(
                "Invalid content: malformed payload detected "
                "(prompt injection)"
            )

    # Strip HTML tags using nh3 (empty allowlist ensures no tags survive)
    clean_str = nh3.clean(input_str, tags=set())

    # Strip any potential script protocol injection (e.g., javascript:alert())
    if "javascript:" in clean_str.lower() or "javascript:" in input_str.lower():
        raise ValueError("Invalid content: script protocols not allowed")

    return clean_str.strip()


def sanitize_html_output(input_str: str) -> str:
    """
    Sanitize text output returned to client to prevent XSS.
    Uses nh3 allowlist to neutralize raw scripts, SVGs, event handlers,
    javascript: protocols, and nested malformed tags.
    """
    if not input_str:
        return input_str

    return nh3.clean(
        input_str,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        url_schemes=ALLOWED_URL_SCHEMES,
        link_rel="noopener noreferrer",
    )
