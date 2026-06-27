"""
Defense-in-depth input sanitizer and output validator for the AI Coach.

Layers:
  1. **normalize_text** — NFKC unicode normalization, strip zero-width chars,
     control characters, and collapse excessive whitespace.
  2. **validate_length** — reject inputs exceeding MAX_INPUT_LENGTH.
  3. **detect_injection** — match against a configurable, categorized list of
     regex patterns loaded from ``injection_patterns.json``.
  4. **validate_output** — post-response check for system-prompt leaks.

The existing ``sanitize_text()`` API is preserved for backward compatibility
(used by Pydantic validators in schemas).

Security logging uses a dedicated ``security.prompt_injection`` logger so
events can be filtered and alerted on separately from general app logs.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import unicodedata
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_INPUT_LENGTH = 1000

# Zero-width and invisible unicode characters commonly used to bypass filters
_ZERO_WIDTH_CHARS = re.compile(
    "["
    "\u200b"  # ZERO WIDTH SPACE
    "\u200c"  # ZERO WIDTH NON-JOINER
    "\u200d"  # ZERO WIDTH JOINER
    "\u200e"  # LEFT-TO-RIGHT MARK
    "\u200f"  # RIGHT-TO-LEFT MARK
    "\u2060"  # WORD JOINER
    "\u2061"  # FUNCTION APPLICATION
    "\u2062"  # INVISIBLE TIMES
    "\u2063"  # INVISIBLE SEPARATOR
    "\u2064"  # INVISIBLE PLUS
    "\ufeff"  # ZERO WIDTH NO-BREAK SPACE (BOM)
    "\u00ad"  # SOFT HYPHEN
    "\u034f"  # COMBINING GRAPHEME JOINER
    "\u061c"  # ARABIC LETTER MARK
    "\u180e"  # MONGOLIAN VOWEL SEPARATOR
    "]"
)

# Non-printable control characters (C0/C1), excluding normal whitespace
_CONTROL_CHARS = re.compile(
    r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]"
)

# Collapse multiple whitespace (spaces, tabs) into single space
_EXCESSIVE_WHITESPACE = re.compile(r"[^\S\n]+")

# Collapse 3+ consecutive newlines into 2
_EXCESSIVE_NEWLINES = re.compile(r"\n{3,}")

# Simple HTML tag stripping (preserved from original)
_HTML_TAG_RE = re.compile(r"<[^>]*>")


# ---------------------------------------------------------------------------
# Custom exceptions (subclass ValueError for backward compat)
# ---------------------------------------------------------------------------

class InputTooLongError(ValueError):
    """Raised when user input exceeds the maximum allowed length."""
    pass


class PromptInjectionError(ValueError):
    """Raised when a prompt injection pattern is detected."""

    def __init__(self, message: str, category: str = "", pattern: str = ""):
        super().__init__(message)
        self.category = category
        self.pattern = pattern


class OutputValidationError(ValueError):
    """Raised when Gemini output fails validation (e.g. system prompt leak)."""
    pass


# ---------------------------------------------------------------------------
# Loggers
# ---------------------------------------------------------------------------

# Standard logger for general sanitizer operations
logger = logging.getLogger(__name__)

# Dedicated security logger — filter on "security.prompt_injection" to
# isolate injection-related events from general app logs.
security_logger = logging.getLogger("security.prompt_injection")


# ---------------------------------------------------------------------------
# Pattern loading
# ---------------------------------------------------------------------------

_PATTERNS_FILE = Path(__file__).parent / "injection_patterns.json"
_compiled_patterns: dict[str, list[tuple[str, re.Pattern]]] | None = None


def _load_patterns(filepath: Path | str | None = None) -> dict[str, list[tuple[str, re.Pattern]]]:
    """
    Load and compile injection patterns from the JSON config file.

    Returns a dict mapping category name → list of (raw_pattern, compiled_regex).
    """
    filepath = Path(filepath) if filepath else _PATTERNS_FILE
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    compiled: dict[str, list[tuple[str, re.Pattern]]] = {}
    for cat_name, cat_data in data.get("categories", {}).items():
        patterns = []
        for raw in cat_data.get("patterns", []):
            try:
                patterns.append((raw, re.compile(raw, re.IGNORECASE)))
            except re.error as e:
                logger.warning(
                    "Invalid regex in injection_patterns.json "
                    "category=%s pattern=%r error=%s", cat_name, raw, e
                )
        compiled[cat_name] = patterns
    return compiled


def _get_patterns() -> dict[str, list[tuple[str, re.Pattern]]]:
    """Return compiled patterns, loading from disk on first call."""
    global _compiled_patterns
    if _compiled_patterns is None:
        _compiled_patterns = _load_patterns()
    return _compiled_patterns


def reload_patterns(filepath: Path | str | None = None) -> None:
    """
    Force-reload patterns from disk.  Useful for testing or hot-reload
    scenarios.
    """
    global _compiled_patterns
    _compiled_patterns = _load_patterns(filepath)


# ---------------------------------------------------------------------------
# Layer 1 — Normalization
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """
    Normalize user input to a canonical form.

    Steps:
      1. NFKC unicode normalization (collapses homoglyphs, compatibility chars)
      2. Strip zero-width / invisible characters
      3. Strip non-printable control characters
      4. Collapse excessive whitespace and newlines
      5. Strip leading/trailing whitespace
    """
    if not text:
        return text

    # NFKC normalization — maps compatibility characters to their canonical
    # forms (e.g. fullwidth latin → ASCII, ligatures → individual chars)
    text = unicodedata.normalize("NFKC", text)

    # Remove zero-width and invisible characters
    text = _ZERO_WIDTH_CHARS.sub("", text)

    # Remove non-printable control characters
    text = _CONTROL_CHARS.sub("", text)

    # Collapse excessive whitespace (preserving single newlines)
    text = _EXCESSIVE_WHITESPACE.sub(" ", text)

    # Collapse 3+ newlines into 2
    text = _EXCESSIVE_NEWLINES.sub("\n\n", text)

    return text.strip()


# ---------------------------------------------------------------------------
# Layer 2 — Length validation
# ---------------------------------------------------------------------------

def validate_length(text: str, max_length: int = MAX_INPUT_LENGTH) -> str:
    """
    Enforce maximum input length.

    Raises ``InputTooLongError`` if the text exceeds ``max_length`` characters.
    """
    if len(text) > max_length:
        raise InputTooLongError(
            f"Input exceeds maximum length of {max_length} characters "
            f"(received {len(text)}). Please shorten your message."
        )
    return text


# ---------------------------------------------------------------------------
# Layer 3 — Pattern-based injection detection
# ---------------------------------------------------------------------------

def detect_injection(
    text: str,
    user_id: Optional[str] = None,
) -> tuple[bool, str, str]:
    """
    Scan normalized text against the configured injection pattern list.

    Returns:
        (is_injection, matched_category, matched_pattern)

    If no injection is detected, returns ``(False, "", "")``.

    When an injection IS detected, the attempt is logged via the security
    logger with the matched category and a truncated/hashed version of the
    input (never the full raw message at INFO level).
    """
    patterns = _get_patterns()

    for category, pattern_list in patterns.items():
        for raw_pattern, compiled in pattern_list:
            if compiled.search(text):
                # --- Security logging ---
                # Hash the input for correlation without logging PII
                input_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
                truncated = text[:80] + "..." if len(text) > 80 else text

                security_logger.warning(
                    "Prompt injection detected | "
                    "category=%s | pattern=%s | "
                    "user_id=%s | input_hash=%s | "
                    "action=blocked",
                    category,
                    raw_pattern,
                    user_id or "unknown",
                    input_hash,
                )
                # Full message only at DEBUG for forensic analysis
                security_logger.debug(
                    "Injection input (truncated): %s", truncated
                )

                # Structured metric line for future Prometheus scraping
                security_logger.info(
                    "METRIC coach_injection_attempts_total "
                    "category=%s action=blocked",
                    category,
                )

                return (True, category, raw_pattern)

    return (False, "", "")


# ---------------------------------------------------------------------------
# Layer 4 — Output validation
# ---------------------------------------------------------------------------

def validate_output(
    response_text: str,
    system_prompt_fragments: list[str] | None = None,
    user_id: Optional[str] = None,
) -> str:
    """
    Validate the Gemini response for system prompt leaks or anomalies.

    Compares the response against known system prompt substrings.  If a
    match is found, logs the incident and raises ``OutputValidationError``.
    """
    if not response_text:
        return response_text

    if system_prompt_fragments is None:
        # Import here to avoid circular imports
        from app.services.prompt_templates import SYSTEM_PROMPT_FRAGMENTS
        system_prompt_fragments = SYSTEM_PROMPT_FRAGMENTS

    response_lower = response_text.lower()
    for fragment in system_prompt_fragments:
        if fragment.lower() in response_lower:
            security_logger.warning(
                "Output validation failed — possible system prompt leak | "
                "matched_fragment=%s | user_id=%s | action=discarded",
                fragment[:40],
                user_id or "unknown",
            )
            security_logger.info(
                "METRIC coach_output_validation_failures_total "
                "reason=system_prompt_leak"
            )
            raise OutputValidationError(
                "Response contained system prompt content"
            )

    return response_text


# ---------------------------------------------------------------------------
# Backward-compatible API — sanitize_text()
# ---------------------------------------------------------------------------

def sanitize_text(input_str: str | None) -> str | None:
    """
    Sanitize user input (backward-compatible entry point).

    Used by Pydantic validators in schemas.  Applies normalization, HTML
    stripping, script/protocol rejection, and injection detection.

    Raises ``ValueError`` (or a subclass) if the input is rejected.
    """
    if input_str is None:
        return None
    if not input_str:
        return input_str

    # Normalize unicode
    text = normalize_text(input_str)

    # Check for scripts (case insensitive) — preserved from original
    if re.search(r"<script.*?>.*?</script>", text, re.IGNORECASE) or "<script" in text.lower():
        raise ValueError("Invalid content: scripts are not allowed")

    # Strip HTML tags
    text = _HTML_TAG_RE.sub("", text)

    # Strip javascript: protocol — preserved from original
    if "javascript:" in text.lower():
        raise ValueError("Invalid content: script protocols not allowed")

    # Injection detection
    is_injection, category, pattern = detect_injection(text)
    if is_injection:
        raise PromptInjectionError(
            "Invalid content: malformed payload detected (prompt injection)",
            category=category,
            pattern=pattern,
        )

    return text.strip()
