#!/usr/bin/env bash
set -euo pipefail

repo_root=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo_root"

required_files=(
  AGENTS.md
  LICENSE
  README.md
  api/README.md
  api/v1/acceptance-vectors.json
  api/v1/acceptance.md
  api/v1/kernel.md
  api/v1/serialization.md
  api/v1/packs/thermal-hvac-v1.md
  api/v1/packs/thermal-hvac-acceptance-vectors.json
  api/v1/packs/storage-bms-v1.md
  api/v1/packs/storage-bms-acceptance-vectors.json
  api/v1/packs/storage-bms-contract-tables.json
  api/v1/packs/pv-inverter-v1.md
  api/v1/packs/pv-inverter-acceptance-vectors.json
  api/v1/packs/evse-v1.md
  api/v1/packs/evse-acceptance-vectors.json
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

if git grep -nE '[[:blank:]]+$' -- '*.json' '*.md' '*.py' '*.sh' '*.yml'; then
  echo "tracked documentation files contain trailing whitespace" >&2
  exit 1
fi

git diff --check
python3 scripts/check_local_links.py
python3 scripts/validate_kernel_v1.py
python3 scripts/check_snapshot_vector_ids.py
python3 scripts/test_check_snapshot_vector_ids.py
python3 scripts/validate_thermal_hvac_pack_v1.py
python3 scripts/test_validate_thermal_hvac_pack_v1.py
python3 scripts/validate_storage_bms_pack_v1.py
python3 scripts/test_validate_storage_bms_pack_v1.py
python3 scripts/validate_pv_inverter_pack_v1.py
python3 scripts/test_validate_pv_inverter_pack_v1.py
python3 scripts/validate_evse_pack_v1.py
python3 scripts/test_validate_evse_pack_v1.py
