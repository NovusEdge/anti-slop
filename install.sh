#!/usr/bin/env bash
# anti-slop installer
# Usage: curl -fsSL https://raw.githubusercontent.com/NovusEdge/anti-slop/main/install.sh | bash
#        ./install.sh --local     # install from this checkout instead of GitHub

set -euo pipefail

REPO="NovusEdge/anti-slop"
MODE="${1:-remote}"

if ! command -v claude &> /dev/null; then
    echo "Error: the 'claude' CLI is not on PATH." >&2
    echo "Install Claude Code first: https://claude.com/claude-code" >&2
    exit 1
fi

if [ "$MODE" = "--local" ]; then
    SOURCE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    SOURCE="$REPO"
fi

echo "Adding marketplace from $SOURCE ..."
if claude plugin marketplace list 2>/dev/null | grep -q '^\s*.\s*anti-slop$'; then
    claude plugin marketplace update anti-slop
else
    claude plugin marketplace add "$SOURCE" --scope user
fi

echo "Installing plugin ..."
claude plugin uninstall anti-slop@anti-slop --scope user >/dev/null 2>&1 || true
claude plugin install anti-slop@anti-slop --scope user

cat <<'EOF'

Installed. Restart Claude Code, then:

  /anti-slop:anti-slop        invoke the skill
  /plugin disable anti-slop   turn the Stop-hook linter off

Standalone linter (no Claude Code needed):

  python3 ~/.claude/plugins/cache/anti-slop/anti-slop/*/tools/lint.py file.md

Pre-commit hook:

  - repo: https://github.com/NovusEdge/anti-slop
    rev: main
    hooks:
      - id: anti-slop
EOF
