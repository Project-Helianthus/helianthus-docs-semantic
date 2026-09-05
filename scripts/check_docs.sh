#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo_root"

required_files=(
  AGENTS.md
  LICENSE
  README.md
  api/README.md
  architecture/repository-ownership-v1.md
  compatibility/donor-ledger.md
  evidence/native-documentation-owners.md
)

for file in "${required_files[@]}"; do
  if [[ ! -s "$file" ]]; then
    echo "required file is missing or empty: $file" >&2
    exit 1
  fi
done

if git grep -nE '[[:blank:]]+$' -- '*.md' '*.py' '*.sh' '*.yml'; then
  echo "tracked documentation files contain trailing whitespace" >&2
  exit 1
fi

git diff --check
python3 scripts/check_local_links.py
