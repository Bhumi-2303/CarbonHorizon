#!/bin/bash
# Pre-commit hook to prevent accidental commit of secrets.
# This scans staged files for common secret patterns followed by non-placeholder values.

set -e

# Define patterns that indicate a secret (case-insensitive)
SECRET_KEYS="(PASSWORD|SECRET_KEY|API_KEY|TOKEN)"

# Define placeholders that are acceptable
PLACEHOLDERS="(changeme|password|example|your_.*_here|replace_.*)"

# Check staged files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

# Find matches for secret keys in the staged files
for FILE in $STAGED_FILES; do
    # Skip binary files or the check-secrets script itself
    if ! git diff --cached "$FILE" | grep -q "^+"; then
        continue
    fi
    
    # We only care about added/modified lines (starting with +)
    # Check if a line contains a secret key assignment
    # e.g., PASSWORD=something or "SECRET_KEY": "something"
    MATCHES=$(git diff --cached "$FILE" | grep -Ei "^\+.*$SECRET_KEYS\s*[:=]\s*[\"']?([^\"'\s]+)[\"']?" || true)
    
    if [ -n "$MATCHES" ]; then
        # Check if the matched value is a placeholder
        while IFS= read -r match; do
            # Extract the assigned value (very simplified parsing for demonstration)
            VALUE=$(echo "$match" | grep -Eo "[:=]\s*[\"']?([^\"'\s]+)[\"']?" | sed -E "s/[:=]\s*[\"']?//; s/[\"']?$//")
            
            if ! echo "$VALUE" | grep -Eiq "^$PLACEHOLDERS$"; then
                # Empty values are sometimes ok (e.g. SECRET_KEY=), but we should warn if it's an obvious hardcoded secret.
                if [ -n "$VALUE" ]; then
                    if [ "$VALUE" == "\${POSTGRES_PASSWORD}" ] || [ "$VALUE" == "\${POSTGRES_USER}" ] || [ "$VALUE" == "\${POSTGRES_DB}" ]; then
                        continue # Docker compose interpolations are fine
                    fi
                    if [[ "$VALUE" == \$\{*\} ]]; then
                       continue # Variable interpolations are fine
                    fi
                    echo -e "\033[1;31mERROR: Potential secret detected in $FILE\033[0m"
                    echo "Line: $match"
                    echo "If this is a false positive, you can bypass with 'git commit --no-verify'"
                    echo "Otherwise, use environment variables and remove the hardcoded secret."
                    exit 1
                fi
            fi
        done <<< "$MATCHES"
    fi
done

exit 0
