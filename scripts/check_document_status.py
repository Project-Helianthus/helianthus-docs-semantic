#!/usr/bin/env python3
"""Enforce quoted status metadata without assigning a status vocabulary."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / 'scripts/document-status-baseline.json'
INITIAL_MISSING = frozenset(['README.md', 'api/README.md', 'api/v1/mappings/growatt-bms-rs485-v202-storage-v1.md', 'api/v1/mappings/huawei-gateway-meter-infrastructure-v1.md', 'api/v1/mappings/huawei-luna2000-storage-v1.md', 'api/v1/mappings/huawei-sun2000-pv-v1.md', 'api/v1/mappings/tesla-gen3-wc3-24443-evse-current-limit-v1.md', 'api/v1/pack-metadata-v1.md', 'api/v1/packs/evse-v1.md', 'api/v1/packs/infrastructure-v1.md', 'api/v1/packs/pv-inverter-v1.md', 'api/v1/packs/storage-bms-v1.md', 'api/v1/packs/thermal-hvac-v1.md', 'api/v1/targets/matter-1.7-ballot-0.9-v1.md', 'author-evidence/issue-16-infrastructure-pack-v1/REPORT.md', 'author-evidence/issue-22-retained-observation-contract/REPORT.md', 'author-evidence/issue-22-sequential-lifecycle-fix-forward/REPORT.md', 'author-evidence/issue-25-growatt-storage-mapping/REPORT.md', 'author-evidence/issue27-tesla-evse-mapping/REPORT.md', 'author-evidence/issue29-pack-metadata-v1/REPORT.md', 'evidence/native-documentation-owners.md'])


def excluded(path):
    return path.name == 'AGENTS.md' or path.name.lower() in {'license.md', 'licence.md', 'legal.md'}


def status(text):
    lines = text.splitlines()
    if not lines or lines[0] != '---':
        return None
    try:
        end = lines.index('---', 1)
    except ValueError as error:
        raise ValueError('unterminated front matter') from error
    header = lines[1:end]
    if len(header) != 1 or not re.fullmatch(r'status: "(?:[^"\\\x00-\x1f]|\\["\\/bfnrt]|\\u[0-9a-fA-F]{4})*"', header[0]):
        raise ValueError('expected exactly one quoted status scalar')
    value = json.loads(header[0][8:])
    if not value.strip():
        raise ValueError('empty status')
    if end + 1 < len(lines) and lines[end + 1] == '---':
        raise ValueError('duplicate header')
    return value


def check(root, baseline, allowed_missing=INITIAL_MISSING):
    errors = []
    paths = {p.relative_to(root).as_posix(): p for p in root.rglob('*.md')
             if '.git' not in p.relative_to(root).parts and '.tmp' not in p.relative_to(root).parts}
    excluded_paths = sorted(k for k, p in paths.items() if excluded(p))
    if excluded_paths != baseline['excluded']:
        errors.append('excluded paths differ from baseline')
    missing = set(baseline['missing_status'])
    if not missing <= allowed_missing or len(missing) != len(baseline['missing_status']):
        errors.append('invalid missing-status baseline')
    for name in sorted(missing - paths.keys()):
        errors.append(f'{name}: stale baseline path')
    for name, path in sorted(paths.items()):
        if excluded(path):
            continue
        try:
            value = status(path.read_text(encoding='utf-8'))
        except (ValueError, json.JSONDecodeError) as error:
            errors.append(f'{name}: {error}')
            continue
        if value is None and name not in missing:
            errors.append(f'{name}: missing status')
        if value is not None and name in missing:
            errors.append(f'{name}: stale missing-status baseline')
    return errors


def main():
    baseline = json.loads(BASELINE.read_text(encoding='utf-8'))
    errors = check(ROOT, baseline)
    print('\n'.join(errors) if errors else 'Document status check passed')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
