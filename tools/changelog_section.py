#!/usr/bin/env python3
"""Print one version's section from docs/CHANGELOG.md.

    python3 tools/changelog_section.py 0.3.0
    python3 tools/changelog_section.py v0.3.0   # a leading v is stripped

release.yml pipes the output into `gh release create --notes-file`.
"""

import sys
from pathlib import Path


def section(text: str, version: str) -> str:
    """Return the body under `## [version]`, up to the next `## [` header.

    Link-reference lines (`[0.3.0]: https://...`) at the file's foot stay out.
    """
    out, capture = [], False
    header = f"## [{version}]"
    for line in text.split("\n"):
        if line.startswith("## ["):
            if capture:
                break
            capture = line.strip().startswith(header)
            continue
        if capture and not line.startswith("["):
            out.append(line)
    return "\n".join(out).strip()


def selftest():
    sample = (
        "# Changelog\n\n"
        "## [0.3.0]\n\n### Added\n- A thing.\n\n"
        "## [0.2.0]\n\n### Added\n- An older thing.\n\n"
        "[0.3.0]: https://example.com/v0.3.0\n"
    )
    assert section(sample, "0.3.0") == "### Added\n- A thing.", "0.3.0 body wrong"
    assert section(sample, "0.2.0") == "### Added\n- An older thing.", "0.2.0 body wrong"
    assert section(sample, "9.9.9") == "", "missing version must be empty"
    print("changelog_section selftest ok")


def main():
    if "--selftest" in sys.argv:
        selftest()
        return
    version = sys.argv[1].lstrip("v")
    path = Path(__file__).resolve().parent.parent / "docs" / "CHANGELOG.md"
    body = section(path.read_text(), version)
    if not body:
        print(f"no changelog section for {version}", file=sys.stderr)
        sys.exit(1)
    print(body)


if __name__ == "__main__":
    main()
