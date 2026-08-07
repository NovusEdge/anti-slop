#!/usr/bin/env python3
"""
anti-slop linter — checks text for AI-generated patterns.

Usage:
    echo "text" | python lint.py
    python lint.py file.md
    python lint.py --check file.md  # exit 1 on violations
"""

import sys
import re
import json
from pathlib import Path

BANNED_WORDS = [
    "delve", "leverage", "harness", "foster", "bolster", "underscore",
    "showcase", "illuminate", "facilitate", "garner", "spearhead",
    "robust", "seamless", "meticulous", "intricate", "comprehensive",
    "pivotal", "crucial", "vital", "multifaceted", "nuanced", "holistic",
    "vibrant", "compelling", "tapestry", "landscape", "realm", "beacon",
    "cornerstone", "backbone", "lifeblood", "paradigm", "interplay",
    "symphony", "moreover", "furthermore", "additionally", "notably",
    "importantly", "fundamentally", "profound", "transformative",
]

BANNED_PHRASES = [
    r"load[- ]bearing",
    r"it'?s not .+, it'?s",
    r"that'?s not .+, that'?s",
    r"less .+, more",
    r"not because .+, but because",
    r"plays a (crucial|vital|key|important) role",
    r"stands as a testament",
    r"serves as a?",
    r"it'?s worth noting",
    r"at its core",
    r"the reality is",
    r"in today'?s fast[- ]paced",
    r"when it comes to",
    r"let'?s dive in",
    r"great question",
    r"you'?re absolutely right",
    r"i hope this finds you well",
    r"certainly!",
    r"absolutely[.!]",
    r"north star",
    r"deep dive",
    r"game[- ]changer",
]

STE_PATTERNS = [
    (r"\b(has|have|had) been \w+ing\b", "perfect progressive tense"),
    (r"\b(has|have|had) been \w+ed\b", "perfect passive"),
    (r"\bwill have \w+ed\b", "future perfect"),
    (r"^[A-Z]\w+ing (the|a|an|\w+)", "-ing sentence opener"),
]


def check_text(text: str, filename: str = "<stdin>") -> list[dict]:
    findings = []
    lines = text.split("\n")

    for i, line in enumerate(lines, 1):
        # Skip code blocks
        if line.strip().startswith("```") or line.strip().startswith("`"):
            continue

        lower = line.lower()

        # Banned words
        for word in BANNED_WORDS:
            if re.search(rf"\b{word}\b", lower):
                findings.append({
                    "file": filename,
                    "line": i,
                    "type": "banned_word",
                    "match": word,
                    "text": line.strip()[:60],
                })

        # Banned phrases
        for pattern in BANNED_PHRASES:
            match = re.search(pattern, lower)
            if match:
                findings.append({
                    "file": filename,
                    "line": i,
                    "type": "banned_phrase",
                    "match": match.group(),
                    "text": line.strip()[:60],
                })

        # STE violations
        for pattern, desc in STE_PATTERNS:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                findings.append({
                    "file": filename,
                    "line": i,
                    "type": "ste_violation",
                    "match": desc,
                    "text": line.strip()[:60],
                })

        # Em-dash frequency (>2 per line)
        if line.count("—") > 2 or line.count("--") > 2:
            findings.append({
                "file": filename,
                "line": i,
                "type": "em_dash_overuse",
                "match": f"{line.count('—') + line.count('--')} em-dashes",
                "text": line.strip()[:60],
            })

    return findings


def format_findings(findings: list[dict], fmt: str = "text") -> str:
    if fmt == "json":
        return json.dumps(findings, indent=2)

    lines = []
    for f in findings:
        lines.append(f"{f['file']}:{f['line']}: [{f['type']}] {f['match']}")
        lines.append(f"  {f['text']}...")
    return "\n".join(lines)


def main():
    check_mode = "--check" in sys.argv
    json_mode = "--json" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    all_findings = []

    if not args or args == ["-"]:
        text = sys.stdin.read()
        all_findings.extend(check_text(text))
    else:
        for arg in args:
            path = Path(arg)
            if path.exists():
                text = path.read_text()
                all_findings.extend(check_text(text, str(path)))
            else:
                print(f"File not found: {arg}", file=sys.stderr)
                sys.exit(1)

    if all_findings:
        fmt = "json" if json_mode else "text"
        print(format_findings(all_findings, fmt))
        if check_mode:
            sys.exit(1)
    else:
        if not json_mode:
            print("No violations found.")


if __name__ == "__main__":
    main()
