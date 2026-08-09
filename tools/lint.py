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

_PATTERNS = json.loads(
    (Path(__file__).resolve().parent.parent / "patterns.json").read_text()
)

# The linter reports the ambiguous words too. Only the Stop hook skips them,
# where a false positive costs a blocked turn.
BANNED_WORDS = _PATTERNS["banned_words"] + _PATTERNS["ambiguous_words"]
BANNED_PHRASES = _PATTERNS["banned_phrases"]
STE_PATTERNS = [(p, d) for p, d in _PATTERNS["ste_patterns"]]
STRUCTURAL = [(p, d) for p, d in _PATTERNS["structural"]]


def check_text(text: str, filename: str = "<stdin>") -> list[dict]:
    # Reference files that quote the banned list opt out with this marker.
    if "anti-slop: ignore-file" in text:
        return []

    findings = []
    lines = text.split("\n")
    in_fence = False

    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue

        # A banned word quoted as an example is not a violation.
        line = re.sub(r"`[^`]*`", "``", line)
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

        # Structural tells
        for pattern, desc in STRUCTURAL:
            match = re.search(pattern, line.strip(), re.IGNORECASE)
            if match:
                findings.append({
                    "file": filename,
                    "line": i,
                    "type": "structural",
                    "match": desc,
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

        # Em-dash frequency (>2 per line). Counts only U+2014; "--" collides
        # with markdown table separators.
        if line.count("—") > 2:
            findings.append({
                "file": filename,
                "line": i,
                "type": "em_dash_overuse",
                "match": f"{line.count('—')} em-dashes",
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


def selftest():
    assert check_text("We leverage the cache."), "banned word missed"
    assert not check_text("We `leverage` the cache."), "inline code not skipped"
    assert not check_text("```\nWe leverage it.\n```"), "fenced block not skipped"
    assert check_text("It's not a cache, it's a buffer."), "contrast form missed"
    assert check_text("Handling the error takes care."), "-ing opener missed"
    assert not check_text("The registry holds one lock per vm."), "false positive"
    print("selftest ok")


def main():
    if "--selftest" in sys.argv:
        selftest()
        return

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
