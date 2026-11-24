"""Read-only git object access. Missing objects are unavailable.

Nothing in this module reads a path from the working tree. Callers that need
a blob ask for ``revision:path`` and receive the object bytes or an error.
"""

from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(Exception):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


def run_git(repo: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if check and completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip()
        raise GitError(detail or f"git {' '.join(args)} failed")
    return completed


def head_sha(repo: Path) -> str:
    completed = run_git(repo, ["rev-parse", "HEAD"])
    return completed.stdout.strip()


def commit_exists(repo: Path, revision: str) -> bool:
    if not revision or any(character.isspace() for character in revision):
        return False
    completed = run_git(repo, ["cat-file", "-e", f"{revision}^{{commit}}"], check=False)
    return completed.returncode == 0


def list_dir(repo: Path, revision: str, directory: str) -> list[str]:
    """Repository-relative names of entries directly inside ``directory``.

    ``git ls-tree`` on a directory path without a trailing slash names the
    directory itself. The slash asks for the entries inside it.
    """
    if directory in ("", "."):
        completed = run_git(repo, ["ls-tree", "--name-only", revision])
        prefix = ""
    else:
        prefix = directory.rstrip("/") + "/"
        completed = run_git(repo, ["ls-tree", "--name-only", revision, prefix])
    names: list[str] = []
    for line in completed.stdout.splitlines():
        if not line:
            continue
        if prefix and not line.startswith(prefix):
            continue
        names.append(line)
    return names


def list_files_recursive(repo: Path, revision: str) -> list[str]:
    completed = run_git(repo, ["ls-tree", "-r", "--name-only", revision])
    return [line for line in completed.stdout.splitlines() if line]


def read_blobs(repo: Path, revision: str, paths: list[str]) -> dict[str, bytes]:
    """Return blobs that exist. Missing paths are omitted."""
    if not paths:
        return {}
    payload = "".join(f"{revision}:{path}\n" for path in paths)
    completed = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "--batch"],
        check=False,
        capture_output=True,
        input=payload.encode(),
    )
    if completed.returncode != 0:
        detail = completed.stderr.decode(errors="replace").strip()
        raise GitError(detail or "git cat-file --batch failed")
    found: dict[str, bytes] = {}
    data = completed.stdout
    cursor = 0
    for path in paths:
        newline = data.find(b"\n", cursor)
        if newline < 0:
            break
        header = data[cursor:newline].decode(errors="replace")
        cursor = newline + 1
        parts = header.split(" ")
        if len(parts) < 3 or parts[-2] != "blob":
            continue
        try:
            size = int(parts[-1])
        except ValueError:
            continue
        blob = data[cursor:cursor + size]
        cursor += size
        if cursor < len(data) and data[cursor:cursor + 1] == b"\n":
            cursor += 1
        found[path] = blob
    return found


def read_blob(repo: Path, revision: str, path: str) -> bytes:
    if not commit_exists(repo, revision):
        raise GitError(f"unavailable: {revision}:{path}")
    found = read_blobs(repo, revision, [path])
    if path not in found:
        raise GitError(f"unavailable: {revision}:{path}")
    return found[path]


def path_exists(repo: Path, revision: str, path: str) -> bool:
    if not commit_exists(repo, revision):
        return False
    return path in read_blobs(repo, revision, [path])
