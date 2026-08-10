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


CODE_COMMENT_SMELLS = [(p, d) for p, d in _PATTERNS["code_comment_smells"]]
CODE_VACUOUS = [(p, d) for p, d in _PATTERNS["code_vacuous"]]
CODE_TEST_SMELLS = [(p, d) for p, d in _PATTERNS["code_test_smells"]]

_HASH = {"line": ["#"], "block": []}
_SLASH = {"line": ["//"], "block": [("/*", "*/")]}
_DASH = {"line": ["--"], "block": []}
COMMENT_SYNTAX = {
    ".py": {"line": ["#"], "block": [('"""', '"""'), ("'''", "'''")]},
    ".sh": _HASH, ".bash": _HASH, ".zsh": _HASH, ".rb": _HASH,
    ".yaml": _HASH, ".yml": _HASH, ".toml": _HASH, ".tf": _HASH,
    ".js": _SLASH, ".jsx": _SLASH, ".ts": _SLASH, ".tsx": _SLASH,
    ".go": _SLASH, ".rs": _SLASH, ".java": _SLASH, ".kt": _SLASH,
    ".c": _SLASH, ".h": _SLASH, ".cc": _SLASH, ".cpp": _SLASH,
    ".cs": _SLASH, ".php": _SLASH, ".swift": _SLASH, ".scala": _SLASH,
    ".sql": _DASH, ".lua": _DASH, ".hs": _DASH,
}

# A string may hold a comment marker. Blanking literals first keeps a url in
# "https://example.com" from reading as the start of a comment.
_STRINGS = re.compile(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'')

_TEST_PATH = re.compile(r"(^|[/_.])(tests?|specs?)([/_.]|$)|(^|/)(test_|conftest)", re.I)


def split_comments(text: str, ext: str) -> tuple[list, list]:
    """Return (comment lines, code lines) as (lineno, text) pairs.

    Line-based, so it misses a comment marker inside a multi-line template
    string. tools/ast_check.py does the exact split for the languages it parses.
    """
    syntax = COMMENT_SYNTAX.get(ext)
    if not syntax:
        return [], []

    comments, code = [], []
    block_end = None
    for i, raw in enumerate(text.split("\n"), 1):
        if block_end:
            comments.append((i, raw.strip()))
            if block_end in raw:
                block_end = None
            continue

        stripped = _STRINGS.sub('""', raw)
        opened = None
        for start, end in syntax["block"]:
            at = stripped.find(start)
            if at != -1 and (opened is None or at < opened[0]):
                opened = (at, start, end)

        cut = None
        for marker in syntax["line"]:
            at = stripped.find(marker)
            if at != -1 and (cut is None or at < cut):
                cut = at
        if opened and (cut is None or opened[0] < cut):
            at, start, end = opened
            rest = raw[at + len(start):]
            comments.append((i, rest.strip()))
            if end not in rest:
                block_end = end
            if raw[:at].strip():
                code.append((i, raw[:at]))
            continue

        if cut is not None:
            comments.append((i, raw[cut:].lstrip("#/- ").strip()))
            if raw[:cut].strip():
                code.append((i, raw[:cut]))
        elif raw.strip():
            code.append((i, raw))
    return comments, code


SKIP_DIRS = {
    ".git", "node_modules", "vendor", "dist", "build", "target",
    "__pycache__", ".venv", "venv", ".tox", ".mypy_cache", "site-packages",
}


def walk_sources(args: list[str]):
    """Yield source files under the given paths, skipping vendored trees."""
    for arg in args:
        path = Path(arg)
        if not path.exists():
            print(f"File not found: {arg}", file=sys.stderr)
            sys.exit(1)
        if path.is_file():
            yield path
            continue
        for child in sorted(path.rglob("*")):
            if child.suffix not in COMMENT_SYNTAX or not child.is_file():
                continue
            if SKIP_DIRS.intersection(child.parts):
                continue
            yield child


def _scan(lines, patterns, kind, filename, findings):
    for lineno, text in lines:
        for pattern, desc in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                findings.append({
                    "file": filename,
                    "line": lineno,
                    "type": kind,
                    "match": desc,
                    "text": text.strip()[:60],
                })


def check_code(text: str, filename: str) -> list[dict]:
    """Lint a source file: comment prose, vacuous code, test assertions."""
    if "anti-slop: ignore-file" in text:
        return []

    ext = Path(filename).suffix
    comments, code = split_comments(text, ext)
    findings: list[dict] = []

    _scan(comments, CODE_COMMENT_SMELLS, "code_comment", filename, findings)
    _scan(code, CODE_VACUOUS, "vacuous_code", filename, findings)
    if _TEST_PATH.search(filename):
        _scan(code, CODE_TEST_SMELLS, "test_smell", filename, findings)

    # A comment is prose. The vocabulary rules apply to it.
    for lineno, comment in comments:
        for finding in check_text(comment, filename):
            finding["line"] = lineno
            findings.append(finding)

    # Two deferral patterns hit one comment. The reader needs the line once.
    seen, unique = set(), []
    for finding in sorted(findings, key=lambda f: (f["line"], f["type"])):
        key = (finding["line"], finding["type"], finding["match"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(finding)
    return unique


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
    code_selftest()
    print("selftest ok")


def code_selftest():
    def hits(text, name="x.py"):
        return {f["match"] for f in check_code(text, name)}

    assert "narrator comment" in hits("# This function handles the request\n")
    assert "step numbering" in hits("# Step 1: Validate the input\n")
    assert "deferral language" in hits("# for now, retry three times\n")
    assert "hedging" in hits("# this should work for most cases\n")
    assert "comparing a boolean to true" in hits("if ok == True:\n")
    assert "comparing a value to itself" in hits("if a == a:\n")

    # A comment marker inside a string is not a comment.
    assert not hits('URL = "https://example.com/#for now"\n')
    # A comment that carries a fact survives.
    assert not hits("# qemu unlinks the monitor socket during Wait().\n")
    # A real equality check between two names is not a tautology.
    assert not hits("if expected == actual:\n")

    test_src = (
        "def test_a():\n"
        "    assert True\n"
        "    assert add(2, 2) == add(2, 2)\n"
        "    mailer.send.assert_called_once()\n"
    )
    found = hits(test_src, "tests/test_a.py")
    assert "assertion that cannot fail" in found
    assert "both sides of the assertion run the same code" in found
    assert "asserting on a mock instead of behaviour" in found
    # The same file outside a test path gets no test rules.
    assert "assertion that cannot fail" not in hits(test_src, "src/a.py")

    assert split_comments("x = 1  // c\n", ".go") == ([(1, "c")], [(1, "x = 1  ")])
    assert split_comments("a = 1\n", ".unknown") == ([], [])


def main():
    if "--selftest" in sys.argv:
        selftest()
        return

    check_mode = "--check" in sys.argv
    json_mode = "--json" in sys.argv
    code_mode = "--code" in sys.argv
    opts = {
        "ambiguous": "--all" in sys.argv,
        "strip_comments": "--strip-comments" in sys.argv,
    }
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    all_findings = []

    if not args or args == ["-"]:
        text = sys.stdin.read()
        all_findings.extend(check_text(text, **opts))
    elif code_mode:
        for path in walk_sources(args):
            all_findings.extend(check_code(path.read_text(errors="replace"), str(path)))
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
