#!/bin/bash
# Pre-commit hook to prevent accidental commit of secrets.
# Uses gitleaks if available, with a fallback to pattern-based checking.

set -e

# 1. First run gitleaks on staged changes if installed
if command -v gitleaks >/dev/null 2>&1; then
    echo "Running gitleaks secret scan on staged changes..."
    gitleaks protect --staged --verbose --redact
    echo "gitleaks scan passed cleanly."
fi

# 2. Secondary layer: scan staged files for common secret patterns followed by non-placeholder values.
SECRET_KEYS="(PASSWORD|SECRET_KEY|API_KEY|TOKEN|PRIVATE_KEY)"
PLACEHOLDERS="(changeme|password|example|your_.*_here|replace_.*|dummy_.*|test_.*|test-.*|mock_.*|mock-.*)"

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

for FILE in $STAGED_FILES; do
    # Skip binary files or the check-secrets script itself
    if ! git diff --cached "$FILE" | grep -q "^+"; then
        continue
    fi

    # Ignore .gitleaks.toml, example templates, test directories, markdown docs
    if [[ "$FILE" == *".env.example"* ]] || [[ "$FILE" == *".gitleaks.toml"* ]] || [[ "$FILE" == *"tests/"* ]] || [[ "$FILE" == *"__tests__/"* ]] || [[ "$FILE" == *".md"* ]]; then
        continue
    fi
    
    MATCHES=$(git diff --cached "$FILE" | grep -Ei "^\+.*$SECRET_KEYS([[:space:]]*:[[:space:]]*[A-Za-z0-9_\[\], ]+)?[[:space:]]*[:=][[:space:]]*[\"']?([^\"'[:space:]]+)[\"']?" || true)
    
    if [ -n "$MATCHES" ]; then
        while IFS= read -r match; do
            # Skip dynamic resolution calls, headers, parameter parsing, comparisons, await calls, object property access, function calls, and type annotations
            if echo "$match" | grep -Eiq "(getattr|resolve_secret|os\.getenv|os\.environ|settings\.|auth\.split|headers|request\.|req\.|data\.|values\.|props\.|formData\.|item\.|user\.|watch\(|Optional\[|Union\[|:[[:space:]]*str|:[[:space:]]*bool|:[[:space:]]*int|:[[:space:]]*float|==|!=|^\+[[:space:]]*(if|elif|assert)\b|await[[:space:]]+)"; then
                continue
            fi
            
            # If the RHS is a function invocation or expression, skip
            if echo "$match" | grep -Eiq "[:=][[:space:]]*[A-Za-z0-9_]+\("; then
                continue
            fi
            
            # Extract assigned value
            VALUE=$(echo "$match" | grep -Eo "[:=][[:space:]]*[\"']?([^\"'[:space:]]+)[\"']?" | sed -E "s/[:=][[:space:]]*[\"']?//; s/[,;\"']+$//; s/^[\"']//")
            
            if ! echo "$VALUE" | grep -Eiq "^$PLACEHOLDERS$"; then
                if [ -n "$VALUE" ]; then
                    if [ "$VALUE" == "\${POSTGRES_PASSWORD}" ] || [ "$VALUE" == "\${POSTGRES_USER}" ] || [ "$VALUE" == "\${POSTGRES_DB}" ]; then
                        continue
                    fi
                    if [[ "$match" =~ \$\{\{.*\}\} ]] || [[ "$VALUE" == \$\{*\} ]]; then
                        continue # GitHub Actions expression or shell variable interpolation
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
