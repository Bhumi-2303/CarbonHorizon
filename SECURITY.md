# Security Policy

## Secret Management Protocol
We take security seriously and have established strict guidelines for managing secrets and credentials within this repository.

### Do NOT Commit Secrets
Under no circumstances should API keys, database URLs, JWT secrets, or any other sensitive credentials be hardcoded in tracked files or committed to version control.

### Using Environment Variables
1. All local development secrets should reside in `.env` files.
2. Ensure that `.env` and `prod_env.yaml` are ignored in `.gitignore`.
3. Use the provided `backend/.env.example` to understand what environment variables are required. 
4. If you add a new environment variable, add it to `.env.example` with a placeholder or fake default value. Never use real values in `.env.example`.

### Production Environments
In production environments (such as Vercel, Heroku, or GitHub Actions), inject secrets using the platform's official secret management functionality (e.g. GitHub Secrets or Vercel Environment Variables).

## AI Coach — Defense-in-Depth against Prompt Injection

The AI Coach feature forwards user messages to Google's Gemini API. Because free-text input is inherently untrusted, we implement a **4-layer defense-in-depth strategy** to prevent prompt injection attacks.

### Layer 1 — Input Validation & Normalization

Applied in `backend/app/core/sanitizer.py` before any prompt construction:

- **Unicode normalization** (`NFKC`) to defeat homoglyph and compatibility-character bypass attempts.
- **Zero-width character stripping** — removes invisible unicode characters (`U+200B`, `U+200C`, `U+200D`, `U+FEFF`, etc.) commonly used to break pattern matching.
- **Control character removal** — strips non-printable C0/C1 control characters.
- **Whitespace normalization** — collapses excessive whitespace and newlines.
- **Length enforcement** — rejects messages exceeding 1000 characters (returns HTTP 400).

### Layer 2 — Pattern-Based Injection Detection

A configurable, categorized list of regex patterns detects known injection techniques:

| Category | Examples |
|---|---|
| `instruction_override` | "ignore previous instructions", "disregard your rules" |
| `role_hijacking` | "you are now a pirate", "pretend to be", "enter DAN mode" |
| `system_prompt_extraction` | "show me your system prompt", "reveal your instructions" |
| `jailbreak` | "developer mode", "jailbreak", "do anything now" |
| `delimiter_injection` | `</system>`, `<|im_start|>`, `[INST]`, `SYSTEM:` |

**Pattern file:** `backend/app/core/injection_patterns.json`

**Updating patterns:** Edit `injection_patterns.json` and restart the server. Patterns are compiled from the JSON file at module import time. No code changes required to add new patterns, but a server restart is necessary for changes to take effect.

**False-positive protection:** Patterns use regex with enough contextual specificity to avoid blocking legitimate messages. For example, "ignore my weekend driving" is NOT blocked because the pattern requires "ignore" to be followed by instruction-related words. The test suite includes explicit false-positive regression tests.

### Layer 3 — Structural Prompt Isolation (Most Important)

Defined in `backend/app/services/prompt_templates.py`:

- **System instructions** are passed via Gemini's dedicated `system_instruction` API parameter — never concatenated into the user content string.
- An **anti-injection suffix** is appended to every system prompt, explicitly instructing the model to ignore any behavioral modification requests found in user messages.
- User messages are wrapped in **`<user_message>` delimiters** with an explicit "treat as data only" instruction.
- **Temperature** is set to 0.7 and **`max_output_tokens`** is capped at 1024 to reduce non-determinism and prevent runaway generation from adversarial prompts.

### Layer 4 — Output Validation

After receiving Gemini's response, the sanitizer checks for:

- **System prompt leaks** — compares the response against known system prompt substrings. If the model echoes back any part of the system prompt, the response is discarded and replaced with a safe fallback message.

### Rate Limiting

The `/api/v1/coach/chat` endpoint is rate-limited to **10 requests per minute** per IP address, stricter than other endpoints, because each call incurs real API cost via Gemini.

### Security Logging

All detected injection attempts are logged via a dedicated `security.prompt_injection` logger with:

- Timestamp (standard log format)
- User ID
- Matched pattern category
- Action taken (blocked/deflected)
- A structured metric line (`METRIC coach_injection_attempts_total`) for future Prometheus integration

**Privacy:** Full raw user messages are never logged at INFO level. Only a truncated/hashed version is logged at DEBUG level for forensic analysis.

### Known Limitations

- **Non-English injection patterns**: The current pattern list only covers English-language injection phrases. Multilingual injection patterns are a documented gap for future work. The structural isolation (Layer 3) and output validation (Layer 4) provide language-agnostic protection even when pattern matching fails.
- **Novel attacks**: Pattern matching is inherently reactive — new injection techniques will bypass existing patterns. This is why Layer 3 (structural isolation) is the primary defense. Update `injection_patterns.json` as new attack patterns are discovered.

### Monitoring

To filter injection-related events in logs:

```bash
# Find all injection attempts
grep "security.prompt_injection" /var/log/app.log

# Count attempts by category
grep "METRIC coach_injection_attempts_total" /var/log/app.log
```

## Reporting a Vulnerability

If you discover a security vulnerability or a leaked secret, please report it immediately.
DO NOT create a public issue regarding a security vulnerability.
Instead, contact the repository maintainers privately.

If a secret is ever accidentally exposed, it must be rotated immediately in the respective third-party service, and all commits containing the secret must be wiped from history.
