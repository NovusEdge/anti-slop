#!/usr/bin/env bash
# anti-slop installer
# Usage: curl -fsSL https://raw.githubusercontent.com/NovusEdge/anti-slop/main/install.sh | bash

set -e

REPO="NovusEdge/anti-slop"
INSTALL_DIR="${HOME}/.claude/plugins/anti-slop"

echo "Installing anti-slop..."

# Check for git
if ! command -v git &> /dev/null; then
    echo "Error: git is required"
    exit 1
fi

# Clone or update
if [ -d "$INSTALL_DIR" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull --ff-only
else
    echo "Cloning to $INSTALL_DIR..."
    mkdir -p "$(dirname "$INSTALL_DIR")"
    git clone "https://github.com/${REPO}.git" "$INSTALL_DIR"
fi

# Make linter executable
chmod +x "$INSTALL_DIR/tools/lint.py"

echo ""
echo "Installed to: $INSTALL_DIR"
echo ""
echo "Usage:"
echo "  /anti-slop           — invoke the skill"
echo "  python ~/.claude/plugins/anti-slop/tools/lint.py file.md"
echo ""
echo "For pre-commit hook, add to .pre-commit-config.yaml:"
echo ""
echo "  - repo: local"
echo "    hooks:"
echo "      - id: anti-slop"
echo "        name: anti-slop"
echo "        entry: python ~/.claude/plugins/anti-slop/tools/lint.py --check"
echo "        language: system"
echo "        types: [markdown]"
echo ""
