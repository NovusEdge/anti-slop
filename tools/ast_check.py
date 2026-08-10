#!/usr/bin/env python3
"""
anti-slop structural checks — the ones a regex cannot see.

    python3 ast_check.py src/
    python3 ast_check.py --check src/        # exit 1 on findings
    python3 ast_check.py --json src/

Python needs nothing installed. The other languages need tree-sitter:

    pip install tree-sitter tree-sitter-language-pack

The plugin installer does not run pip, so tree-sitter stays optional. Without
it, this checks Python and names the files it skipped.
"""

import ast
import io
import json
import re
import sys
import tokenize
from pathlib import Path

TS_LANGUAGES = {
    ".js": "javascript", ".jsx": "javascript", ".ts": "typescript",
    ".tsx": "tsx", ".go": "go", ".rs": "rust", ".java": "java",
    ".c": "c", ".cpp": "cpp", ".rb": "ruby", ".php": "php",
}
SKIP_DIRS = {
    ".git", "node_modules", "vendor", "dist", "build", "target",
    "__pycache__", ".venv", "venv", ".tox", ".mypy_cache", "site-packages",
}

# A comment that maps entirely onto the statement below carries no fact. These
# map an operation to the words a paraphrase uses for it.
OP_WORDS = {
    "AugAssign+": {"increment", "add", "bump", "raise", "up"},
    "AugAssign-": {"decrement", "subtract", "reduce", "lower", "down"},
    "Assign": {"set", "assign", "initialize", "init", "create", "define", "store", "declare"},
    "Return": {"return", "give", "yield", "produce"},
    "If": {"check", "test", "verify", "handle", "case", "when"},
    "For": {"loop", "iterate", "each", "every", "over", "through"},
    "While": {"loop", "iterate", "until", "while", "repeat"},
    "Import": {"import", "load", "include", "require"},
    "FunctionDef": {"function", "method", "define", "helper", "handle"},
    "ClassDef": {"class", "define", "represent"},
    "Call": {"call", "invoke", "run", "execute", "perform"},
    "Raise": {"raise", "throw", "error", "fail"},
    "Try": {"try", "catch", "handle", "attempt"},
}
STOP_WORDS = {
    "a", "an", "the", "to", "of", "for", "in", "on", "at", "by", "is", "are",
    "we", "this", "that", "it", "its", "and", "or", "if", "then", "with",
    "from", "as", "be", "will", "now", "here", "up", "out", "into", "s",
}
# Filler nouns a paraphrase reaches for when the code has no word for the thing:
# "increment the retry counter" over `retries += 1`. Counting them would dilute
# the ratio and let the paraphrase through.
GENERIC_NOUNS = {
    "counter", "count", "index", "flag", "value", "values", "variable", "var",
    "list", "array", "dict", "map", "set", "number", "result", "results",
    "object", "obj", "string", "str", "item", "items", "field", "method",
    "function", "func", "parameter", "param", "argument", "arg", "data",
    "instance", "element", "entry", "key", "pair", "state", "status", "output",
    "input", "response", "request", "class", "attribute", "property", "type",
}


def stem(word: str) -> str:
    word = word.lower()
    for suffix in ("ies", "ing", "ed", "es", "s", "ly"):
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            return word[: -len(suffix)] + ("y" if suffix == "ies" else "")
    return word


def split_identifier(name: str) -> set[str]:
    parts = re.split(r"[_\W]+", re.sub(r"(?<!^)(?=[A-Z])", "_", name))
    return {stem(p) for p in parts if p}


def comment_words(text: str) -> list[str]:
    text = re.sub(r"^[#/*\-\s]+", "", text).strip().rstrip("*/").strip()
    words = re.findall(r"[A-Za-z_][A-Za-z_0-9]*", text)
    return [
        w for w in words
        if w.lower() not in STOP_WORDS and stem(w) not in GENERIC_NOUNS
    ]


class Finding(dict):
    def __init__(self, file, line, kind, message, text=""):
        super().__init__(file=file, line=line, type=kind, match=message, text=text[:70])


# ---------------------------------------------------------------- python

def python_findings(source: str, filename: str) -> list[Finding]:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return [Finding(filename, exc.lineno or 1, "parse_error", f"cannot parse: {exc.msg}")]

    lines = source.split("\n")
    findings: list[Finding] = []
    findings += _paraphrase(source, tree, filename, lines)
    findings += _blank_runs(tree, filename, lines)

    for node in ast.walk(tree):
        findings += _vacuous_node(node, filename, lines)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            findings += _duplicate_values(node, filename, lines)
    return findings


def _statement_vocabulary(node: ast.AST) -> set[str]:
    """Words a paraphrase of this statement would use."""
    vocab: set[str] = set()
    kind = type(node).__name__
    if isinstance(node, ast.AugAssign):
        sign = "+" if isinstance(node.op, ast.Add) else "-"
        vocab |= OP_WORDS.get(f"AugAssign{sign}", set())
    elif isinstance(node, (ast.Import, ast.ImportFrom)):
        vocab |= OP_WORDS["Import"]
    elif kind in OP_WORDS:
        vocab |= OP_WORDS[kind]
    if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
        vocab |= OP_WORDS["Call"]

    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            vocab |= split_identifier(child.id)
        elif isinstance(child, ast.Attribute):
            vocab |= split_identifier(child.attr)
        elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            vocab |= split_identifier(child.name)
        elif isinstance(child, ast.arg):
            vocab |= split_identifier(child.arg)
        elif isinstance(child, ast.alias):
            vocab |= split_identifier(child.name.split(".")[-1])
    return vocab


def _paraphrase(source, tree, filename, lines) -> list[Finding]:
    """A comment whose words all come from the statement it introduces."""
    starts: dict[int, ast.AST] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.stmt) and node.lineno not in starts:
            starts[node.lineno] = node

    findings = []
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError):
        return findings

    for token in tokens:
        if token.type != tokenize.COMMENT:
            continue
        line = token.start[0]
        # Only a comment on its own line introduces the statement below it.
        if lines[line - 1].strip() != token.string.strip():
            continue
        target = next((starts[n] for n in range(line + 1, line + 3) if n in starts), None)
        if target is None:
            continue

        words = comment_words(token.string)
        if not (1 <= len(words) <= 9):
            continue
        vocab = _statement_vocabulary(target)
        covered = sum(1 for w in words if stem(w) in vocab)
        if covered == len(words) or (len(words) >= 3 and covered / len(words) >= 0.75):
            findings.append(
                Finding(filename, line, "paraphrase_comment",
                        "comment restates the statement below", token.string)
            )
    return findings


def _blank_runs(tree, filename, lines) -> list[Finding]:
    """Two or more blank lines inside a function body separate nothing."""
    findings = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        end = getattr(node, "end_lineno", None) or node.lineno
        run_start, run = None, 0
        for i in range(node.body[0].lineno, end + 1):
            if i <= len(lines) and not lines[i - 1].strip():
                run_start = run_start or i
                run += 1
            else:
                if run >= 2:
                    findings.append(
                        Finding(filename, run_start, "blank_line_run",
                                f"{run} blank lines inside {node.name}()")
                    )
                run_start, run = None, 0
    return findings


def _duplicate_values(func, filename, lines) -> list[Finding]:
    """Two names in one function body bound to the same expression."""
    by_source: dict[str, str] = {}
    findings = []
    for node in func.body:
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1):
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        try:
            source = ast.unparse(node.value)
        except Exception:
            continue
        if isinstance(node.value, (ast.Constant,)) and node.value.value in (None, True, False, 0, 1, "", []):
            continue  # a shared sentinel is ordinary
        if source == target.id:
            continue
        first = by_source.get(source)
        if first and first != target.id:
            findings.append(
                Finding(filename, node.lineno, "duplicate_value",
                        f"{target.id} repeats the value already in {first}",
                        lines[node.lineno - 1] if node.lineno <= len(lines) else "")
            )
        else:
            by_source[source] = target.id
    return findings


def _is_bool(node, value) -> bool:
    return isinstance(node, ast.Constant) and node.value is value


def _vacuous_node(node, filename, lines) -> list[Finding]:
    lineno = getattr(node, "lineno", 0)
    text = lines[lineno - 1] if 0 < lineno <= len(lines) else ""
    out = []

    if isinstance(node, ast.Try):
        for handler in node.handlers:
            body = handler.body
            at = handler.lineno
            handler_text = lines[at - 1] if 0 < at <= len(lines) else ""
            if len(body) == 1 and isinstance(body[0], ast.Pass):
                out.append(Finding(filename, at, "silent_handler",
                                   "except body is pass; the error disappears",
                                   handler_text))
            elif (
                len(body) == 1
                and isinstance(body[0], ast.Raise)
                and isinstance(body[0].exc, ast.Name)
                and handler.name == body[0].exc.id
            ):
                out.append(Finding(filename, at, "vacuous_handler",
                                   "catch and re-raise unchanged", handler_text))

    if isinstance(node, ast.If):
        body, orelse = node.body, node.orelse
        if (
            len(body) == 1 and len(orelse) == 1
            and isinstance(body[0], ast.Return) and isinstance(orelse[0], ast.Return)
            and _is_bool(body[0].value, True) and _is_bool(orelse[0].value, False)
        ):
            out.append(Finding(filename, node.lineno, "vacuous_branch",
                               "return the condition instead of True/False", text))
        elif orelse and _same_source(body, orelse):
            out.append(Finding(filename, node.lineno, "vacuous_branch",
                               "both branches have the same body", text))
        if isinstance(node.test, ast.Compare) and len(node.test.ops) == 1:
            try:
                if ast.unparse(node.test.left) == ast.unparse(node.test.comparators[0]):
                    out.append(Finding(filename, node.lineno, "vacuous_condition",
                                       "condition compares a value to itself", text))
            except Exception:
                pass
    return out


def _same_source(a, b) -> bool:
    try:
        return [ast.unparse(n) for n in a] == [ast.unparse(n) for n in b]
    except Exception:
        return False


# ------------------------------------------------------------ tree-sitter

def load_tree_sitter():
    try:
        from tree_sitter_language_pack import get_parser
    except ImportError:
        return None
    return get_parser


def treesitter_findings(source: str, filename: str, language: str, get_parser) -> list[Finding]:
    """Comment paraphrase and blank-line runs for a non-Python file."""
    try:
        parser = get_parser(language)
    except Exception:
        return []
    tree = parser.parse(source.encode())
    lines = source.split("\n")
    findings = []

    comments, functions = [], []

    def walk(node):
        if node.type == "comment" or node.type.endswith("comment"):
            comments.append(node)
        if "function" in node.type or "method" in node.type:
            functions.append(node)
        for child in node.children:
            walk(child)

    walk(tree.root_node)

    for comment in comments:
        line = comment.start_point[0] + 1
        if lines[line - 1].strip() != comment.text.decode(errors="replace").strip():
            continue
        words = comment_words(comment.text.decode(errors="replace"))
        if not (1 <= len(words) <= 9):
            continue
        following = "\n".join(lines[line : line + 2])
        vocab = {stem(p) for ident in re.findall(r"[A-Za-z_][A-Za-z_0-9]*", following)
                 for p in split_identifier(ident)}
        for op, op_words in OP_WORDS.items():
            if op == "Return" and "return" in following:
                vocab |= op_words
            if op == "If" and re.search(r"\bif\b", following):
                vocab |= op_words
            if op == "For" and re.search(r"\b(for|while)\b", following):
                vocab |= op_words
        covered = sum(1 for w in words if stem(w) in vocab)
        if covered == len(words) or (len(words) >= 3 and covered / len(words) >= 0.75):
            findings.append(Finding(filename, line, "paraphrase_comment",
                                    "comment restates the statement below",
                                    comment.text.decode(errors="replace")))

    for func in functions:
        start, end = func.start_point[0] + 1, func.end_point[0] + 1
        run_start, run = None, 0
        for i in range(start, min(end, len(lines)) + 1):
            if not lines[i - 1].strip():
                run_start = run_start or i
                run += 1
            else:
                if run >= 2:
                    findings.append(Finding(filename, run_start, "blank_line_run",
                                            f"{run} blank lines inside a function body"))
                run_start, run = None, 0
    return findings


# ------------------------------------------------------------------ cli

def walk_sources(args):
    for arg in args:
        path = Path(arg)
        if not path.exists():
            print(f"File not found: {arg}", file=sys.stderr)
            sys.exit(1)
        if path.is_file():
            yield path
            continue
        for child in sorted(path.rglob("*")):
            if not child.is_file() or SKIP_DIRS.intersection(child.parts):
                continue
            if child.suffix == ".py" or child.suffix in TS_LANGUAGES:
                yield child


def check_file(path: Path, get_parser) -> tuple[list[Finding], bool]:
    """Returns (findings, skipped). skipped means tree-sitter was missing."""
    source = path.read_text(errors="replace")
    if "anti-slop: ignore-file" in source:
        return [], False
    if path.suffix == ".py":
        return python_findings(source, str(path)), False
    language = TS_LANGUAGES.get(path.suffix)
    if not language:
        return [], False
    if get_parser is None:
        return [], True
    return treesitter_findings(source, str(path), language, get_parser), False


def selftest():
    src = (
        "import os\n"
        "\n"
        "def handle(payload, retries):\n"
        "    # increment the retry counter\n"
        "    retries += 1\n"
        "\n"
        "\n"
        "    result = compute(payload)\n"
        "    value = compute(payload)\n"
        "    if retries == retries:\n"
        "        return None\n"
        "    # Legacy rows predate the NOT NULL migration.\n"
        "    if payload.ok:\n"
        "        return True\n"
        "    else:\n"
        "        return False\n"
        "\n"
        "def risky():\n"
        "    try:\n"
        "        run()\n"
        "    except ValueError:\n"
        "        pass\n"
    )
    kinds = {f["type"] for f in python_findings(src, "x.py")}
    assert "paraphrase_comment" in kinds, "paraphrase missed"
    assert "blank_line_run" in kinds, "blank run missed"
    assert "duplicate_value" in kinds, "duplicate value missed"
    assert "vacuous_condition" in kinds, "self-comparison missed"
    assert "vacuous_branch" in kinds, "True/False branch missed"
    assert "silent_handler" in kinds, "silent handler missed"

    messages = [f["match"] for f in python_findings(src, "x.py")]
    assert not any("Legacy rows" in m for m in messages), "real comment flagged"

    # A comment carrying an outside fact survives next to the code it explains.
    keeper = (
        "def stop(vm):\n"
        "    # qemu unlinks the monitor socket during Wait().\n"
        "    vm.stop()\n"
    )
    assert not python_findings(keeper, "k.py"), "fact-carrying comment flagged"

    # Ordinary code produces nothing.
    clean = (
        "def load(path):\n"
        "    text = path.read_text()\n"
        "    if not text.strip():\n"
        "        raise ConfigError(path)\n"
        "    return parse(text)\n"
    )
    assert not python_findings(clean, "c.py"), "false positive on clean code"
    print("ast selftest ok")


def main():
    if "--selftest" in sys.argv:
        selftest()
        return

    check_mode = "--check" in sys.argv
    json_mode = "--json" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")] or ["."]

    get_parser = load_tree_sitter()
    findings, skipped = [], []
    for path in walk_sources(args):
        found, was_skipped = check_file(path, get_parser)
        findings.extend(found)
        if was_skipped:
            skipped.append(str(path))

    if json_mode:
        print(json.dumps(findings, indent=2))
    else:
        for f in findings:
            print(f"{f['file']}:{f['line']}: [{f['type']}] {f['match']}")
            if f["text"]:
                print(f"  {f['text'].strip()}")
        if skipped:
            print(
                f"\n{len(skipped)} non-Python file(s) skipped. For those languages:\n"
                "  pip install tree-sitter tree-sitter-language-pack",
                file=sys.stderr,
            )
        if not findings:
            print("No findings.")

    if findings and check_mode:
        sys.exit(1)


if __name__ == "__main__":
    main()
