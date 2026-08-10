#!/usr/bin/env python3
"""
anti-slop linter — checks text for AI-generated patterns.

Usage:
    echo "text" | python lint.py
    python lint.py file.md
    python lint.py --check file.md           # exit 1 on violations
    python lint.py --all file.md             # add the ambiguous words
    python lint.py --strip-comments MSG      # skip # lines (commit messages)
"""

import sys
import re
import json
from pathlib import Path

_PATTERNS = json.loads(
    (Path(__file__).resolve().parent.parent / "patterns.json").read_text()
)


# Model output uses curly quotes. Every apostrophe pattern here is written with
# a straight quote, so "It’s not X, it’s Y" escaped the whole contrast set.
_QUOTES = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"'})


def normalize(text: str) -> str:
    return text.translate(_QUOTES)


def inflect(word: str) -> str:
    """Regex for a stem and its inflections.

    The lists hold stems. A bare \\b stem\\b missed "leverages", "delving" and
    "fostered", which is most of how the words appear.
    """
    if word.endswith("ic"):
        return rf"{word}(?:ally|s)?"
    if word.endswith("e"):
        return rf"{word[:-1]}(?:e|es|ed|ing|ely)"
    # A consonant before the y takes -ies: tapestry, tapestries.
    if word.endswith("y") and word[-2] not in "aeiou":
        return rf"(?:{word}|{word[:-1]}ies)"
    return rf"{word}(?:s|es|ed|ing|ly)?"


BANNED_WORDS = _PATTERNS["banned_words"]
# "robust", "harness" and "landscape" are real technical words. They stay behind
# --all, so --check can gate a commit without failing on ordinary prose.
AMBIGUOUS_WORDS = _PATTERNS["ambiguous_words"]
# set name -> finding type. Naming the tier teaches more than one flat "phrase".
PHRASE_SETS = _PATTERNS["_phrase_sets"]
STE_PATTERNS = [(p, d) for p, d in _PATTERNS["ste_patterns"]]
STRUCTURAL = [(p, d) for p, d in _PATTERNS["structural"]]


def check_text(
    text: str,
    filename: str = "<stdin>",
    ambiguous: bool = False,
    strip_comments: bool = False,
) -> list[dict]:
    # Reference files that quote the banned list opt out with this marker.
    if "anti-slop: ignore-file" in text:
        return []

    words = BANNED_WORDS + AMBIGUOUS_WORDS if ambiguous else BANNED_WORDS
    findings = []
    lines = normalize(text).split("\n")
    in_fence = False

    for i, line in enumerate(lines, 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        # git commit -v writes the whole diff into the message file below the
        # comment block. Every diff line would otherwise be linted as prose.
        if strip_comments and line.startswith("#"):
            continue

        # Code, quoted examples and blockquotes are not the writer's own prose.
        # A double-quoted span is how you cite slop, and banned words are this
        # tool's whole subject. Mirrors prosify() in hooks/check.js.
        if line.lstrip().startswith(">"):
            continue
        line = re.sub(r"`[^`]*`", "``", line)
        line = re.sub(r'"[^"]*"', '""', line)
        lower = line.lower()

        # Banned words
        for word in words:
            if re.search(rf"\b{inflect(word)}\b", lower):
                findings.append({
                    "file": filename,
                    "line": i,
                    "type": (
                        "ambiguous_word" if word in AMBIGUOUS_WORDS else "banned_word"
                    ),
                    "match": word,
                    "text": line.strip()[:60],
                })

        # Banned phrases and sycophancy
        for set_name, spec in PHRASE_SETS.items():
            if "lint" not in spec["tools"]:
                continue
            for entry in _PATTERNS[set_name]:
                pattern, desc = entry if isinstance(entry, list) else (entry, None)
                match = re.search(pattern, lower)
                if match:
                    findings.append({
                        "file": filename,
                        "line": i,
                        "type": spec["kind"],
                        "match": desc or match.group().strip(),
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

        # STE violations. Case-sensitive: the -ing rule anchors on a capital,
        # and IGNORECASE made it fire on "nothing", "during" and "something".
        for pattern, desc in STE_PATTERNS:
            match = re.search(pattern, line)
            if match:
                findings.append({
                    "file": filename,
                    "line": i,
                    "type": "ste_violation",
                    "match": desc,
                    "text": line.strip()[:60],
                })

        # Em-dash frequency. A markdown paragraph is one line, so this counts
        # per paragraph. Two is the parenthetical pair, which reads fine.
        # Counts only U+2014; "--" collides with markdown table separators.
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


def corpus_test():
    path = Path(__file__).resolve().parent.parent / "tests" / "corpus.json"
    cases = json.loads(path.read_text())["cases"]
    ran = 0
    for case in cases:
        if "lint" not in case["tools"]:
            continue
        ran += 1
        got = bool(check_text(case["text"]))
        assert got == case["hit"], (
            f"corpus: expected hit={case['hit']} ({case['why']}) "
            f"for {case['text']!r}"
        )
    print(f"corpus ok ({ran} cases)")


def selftest():
    corpus_test()
    assert check_text("We leverage the cache."), "banned word missed"
    assert not check_text("We `leverage` the cache."), "inline code not skipped"
    assert not check_text("```\nWe leverage it.\n```"), "fenced block not skipped"
    assert check_text("It's not a cache, it's a buffer."), "contrast form missed"
    assert check_text("Handling the error takes care."), "-ing opener missed"
    assert not check_text("Nothing the code does is safe."), "-ing false positive"
    assert not check_text("During the merge the lock is held."), "-ing false positive"
    assert check_text("The socket has been closed."), "perfect passive missed"
    assert not check_text("The registry holds one lock per vm."), "false positive"
    assert check_text("Say the word and I'll add it."), "servile closer missed"
    assert not check_text("Postgres or SQLite?"), "plain question flagged"
    assert not check_text("A robust retry covers it."), "ambiguous word on by default"
    assert check_text("A robust retry covers it.", ambiguous=True), "--all missed it"
    assert not check_text(
        "# We leverage the cache", strip_comments=True
    ), "comment line not skipped"
    print("selftest ok")


def main():
    if "--selftest" in sys.argv:
        selftest()
        return

    check_mode = "--check" in sys.argv
    json_mode = "--json" in sys.argv
    opts = {
        "ambiguous": "--all" in sys.argv,
        "strip_comments": "--strip-comments" in sys.argv,
    }
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    all_findings = []

    if not args or args == ["-"]:
        text = sys.stdin.read()
        all_findings.extend(check_text(text, **opts))
    else:
        for arg in args:
            path = Path(arg)
            if path.exists():
                text = path.read_text()
                all_findings.extend(check_text(text, str(path), **opts))
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
