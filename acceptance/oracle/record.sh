#!/usr/bin/env bash
# Record the outputs of one reference (items 3 to 9, 12).
#   record.sh <reference>                 initial recording into acceptance/vectors and acceptance/oracle
#   record.sh <reference> --replay [--no-sessions]
#                                         every actual output goes under .tmp/oracle-replay/<reference>/, never into acceptance/vectors
# Environment: ORACLE_DONOR_ROOT names the directory with one clone per slug_at_pin; GOMODCACHE names a module cache that holds
# the public module sources (no network is used).
set -euo pipefail
reference="${1:?usage: record.sh <current|released|pre-port> [--replay] [--no-sessions]}"
shift || true
here="$(cd "$(dirname "$0")" && pwd)"
root="$(cd "$here/../.." && pwd)"
replay=0
extra=()
for argument in "$@"; do
  case "$argument" in
    --replay) replay=1 ;;
    --no-sessions) extra+=(--no-sessions) ;;
    *) echo "unknown argument $argument" >&2; exit 2 ;;
  esac
done
: "${ORACLE_DONOR_ROOT:?ORACLE_DONOR_ROOT is not set}"
export ORACLE_SCRATCH="${ORACLE_SCRATCH:-$root/.tmp/oracle-scratch}"
export GOWORK=off
if [ "$replay" = 1 ]; then
  target="$root/.tmp/oracle-replay/$reference"
  python3 - "$target" <<'PY'
import shutil, sys
from pathlib import Path
target = Path(sys.argv[1])
if target.exists():
    shutil.rmtree(target)
PY
  vectors="$target/vectors"; oracle="$target/oracle"
else
  vectors="$root/acceptance/vectors"; oracle="$here"
fi
mkdir -p "$vectors" "$oracle"
python3 -I "$here/recorders/run_all.py" --reference "$reference" --vectors "$vectors" --oracle "$oracle" --entries "$root/.tmp/oracle-entries-$reference.json" ${extra[@]+"${extra[@]}"}
