#!/usr/bin/env python3
"""Check repository-local Markdown links without querying the network."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parent.parent
LINK = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")


def markdown_files() -> list[Path]:
    output = subprocess.check_output(
        ["git", "ls-files", "*.md"], cwd=ROOT, text=True
    )
    return [ROOT / line for line in output.splitlines() if line]


def local_target(raw_target: str) -> str | None:
    target = raw_target.strip()
    if target.startswith("<") and target.endswith(">"):
        target = target[1:-1]
    elif " " in target:
        target = target.split(" ", 1)[0]

    if not target or target.startswith(("#", "https://", "http://", "mailto:")):
        return None
    if target.startswith(("/", "file:")):
        raise ValueError(f"non-portable local link: {raw_target}")
    return unquote(target.split("#", 1)[0])


def main() -> None:
    failures: list[str] = []
    for document in markdown_files():
        text = document.read_text(encoding="utf-8")
        for raw_target in LINK.findall(text):
            try:
                target = local_target(raw_target)
            except ValueError as error:
                failures.append(f"{document.relative_to(ROOT)}: {error}")
                continue
            if target is None:
                continue

            resolved = (document.parent / target).resolve()
            try:
                resolved.relative_to(ROOT)
            except ValueError:
                failures.append(
                    f"{document.relative_to(ROOT)}: link escapes repository: {raw_target}"
                )
                continue
            if not resolved.exists():
                failures.append(
                    f"{document.relative_to(ROOT)}: missing link target: {raw_target}"
                )

    if failures:
        raise SystemExit("\n".join(failures))


if __name__ == "__main__":
    main()
