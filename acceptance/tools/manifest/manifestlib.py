"""Generate, check, compare, receipt and deletion for sealed move manifests."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import closure
import gitstore
import patterns as patternlib

TEMPLATE_KEYS = ("origin", "quality", "source", "timing", "provenance")
BINDING_ROLES = ("donor-native", "new-binding", "caller-template")
MAPPING_KINDS = ("donor-backed", "specification", "binding")
CLASSIFIER_PREFIXES = ("cmd/growatt-can-classify", "internal/growattcanclassify")
CLASSIFIER_SURFACES = (
    "local-file",
    "stdin",
    "json",
    "text",
    "monitor-association",
    "error-stdout",
    "error-stderr",
    "status",
)
GG11_DIR = "scripts/fixtures/transport-gate/matter-feed-gateway-sources"
DELETION_ROWS = ("GG07", "GG08", "GG09", "GG10", "GG11", "GG13")
SHARED_PRODUCTION = (
    "cmd/gateway/leaf_promotion_live_source.go",
    "internal/promotion/registry.go",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def manifest_dir() -> Path:
    return repo_root() / "acceptance" / "manifests"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def dump(value: Any) -> str:
    return json.dumps(value, indent=2, ensure_ascii=True) + "\n"


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def list_bytes(paths: list[str]) -> bytes:
    ordered = sorted(set(paths))
    if any("*" in path or "?" in path for path in ordered):
        raise ValueError("sealed path contains a glob")
    if not ordered:
        return b""
    return ("".join(path + "\n" for path in ordered)).encode()


def emit(lines: list[str]) -> int:
    unique = sorted(set(lines))
    text = "".join(line + "\n" for line in unique)
    import sys
    sys.stdout.write(text)
    return 1 if unique else 0


def _blob(repo: Path, revision: str, path: str) -> bytes:
    try:
        return gitstore.read_blob(repo, revision, path)
    except gitstore.GitError as error:
        raise KeyError(f"unavailable: {revision}:{path}") from error


def _projection_for(role: str, blob: bytes) -> dict[str, Any]:
    data = json.loads(blob.decode())
    if not isinstance(data, dict):
        raise ValueError(f"reference {role} is not an object")
    if role == "donor-native":
        return {"fields": data}
    if role == "new-binding":
        leaked = [key for key in TEMPLATE_KEYS if key in data]
        if leaked:
            raise ValueError("binding-has-template: " + ",".join(leaked))
        for key in ("key", "subject", "value"):
            if key not in data:
                raise ValueError(f"binding-operand: {key}")
        return {"key": data["key"], "subject": data["subject"], "value": data["value"]}
    if role == "caller-template":
        missing = [key for key in TEMPLATE_KEYS if key not in data]
        if missing:
            raise ValueError("template-operand: " + ",".join(missing))
        return {key: data[key] for key in TEMPLATE_KEYS}
    if role == "donor-output":
        if "fields" not in data:
            raise ValueError("donor-output-fields")
        return {"fields": data["fields"], "status": data.get("status")}
    if role == "specification":
        if "status" in data or "donor_output" in data or "donor_symbol" in data:
            raise ValueError("specification-has-donor-status")
        return {
            "fields": data.get("fields", {}),
            "inputs": data.get("inputs", {}),
            "selectors": data.get("selectors", {}),
        }
    if role == "expected-difference":
        return data
    if role == "candidate":
        return data
    raise ValueError(f"unknown reference role: {role}")


def _record_reference(tool: Path, reference: dict[str, Any]) -> dict[str, Any]:
    revision = reference["revision"]
    path = reference["path"]
    try:
        blob = _blob(tool, revision, path)
    except KeyError:
        raise KeyError(f"unavailable: {reference.get('repository', '')}:{path}") from None
    role = reference["role"]
    try:
        projection = _projection_for(role, blob)
    except ValueError as error:
        raise ValueError(str(error)) from error
    recorded = {
        "role": role,
        "repository": reference["repository"],
        "revision": revision,
        "path": path,
        "blob_sha256": digest(blob),
        "projection": projection,
    }
    return recorded


def _reload_reference(tool: Path, recorded: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    try:
        blob = _blob(tool, recorded["revision"], recorded["path"])
    except KeyError:
        return None, f"unavailable: {recorded['repository']}:{recorded['path']}"
    if digest(blob) != recorded.get("blob_sha256"):
        return None, f"mutated: {recorded['repository']}:{recorded['path']}"
    try:
        projection = _projection_for(recorded["role"], blob)
    except ValueError as error:
        return None, str(error)
    if patternlib.canonical(projection) != patternlib.canonical(recorded.get("projection")):
        return None, f"mutated: {recorded['repository']}:{recorded['path']}"
    return projection, None


def _difference_fields(source: dict[str, Any]) -> dict[str, Any]:
    """Case, field, presence, values, source and approval of one vector."""
    return {
        "case": source.get("case"),
        "field": source.get("field"),
        "old_present": bool(source.get("old_present", True)),
        "old": source.get("old"),
        "new": source.get("new"),
        "source": source.get("source"),
        "approval": source.get("approval"),
    }


def _difference_agrees(entry: dict[str, Any], projection: dict[str, Any]) -> bool:
    recorded = _difference_fields(entry)
    pinned = _difference_fields(projection)
    for key in ("case", "field", "source", "approval", "new", "old_present"):
        if recorded[key] != pinned[key]:
            return False
    if recorded["old_present"] and recorded["old"] != pinned["old"]:
        return False
    return True


def _revalidate_difference(
    tool: Path, entry: dict[str, Any]
) -> tuple[dict[str, Any] | None, str | None]:
    """Vector taken from its reloaded reference, or why that reference was refused.

    The top-level case, field, presence, values, source and approval must equal
    the reference. Callers consume this vector and not the top-level copy.
    """
    recorded = entry.get("reference")
    if not isinstance(recorded, dict):
        return None, "mutated: :"
    projection, problem = _reload_reference(tool, recorded)
    if problem or projection is None:
        return None, problem or f"mutated: {recorded.get('repository', '')}:{recorded.get('path', '')}"
    if not _difference_agrees(entry, projection):
        return None, f"mutated: {recorded.get('repository', '')}:{recorded.get('path', '')}"
    return _difference_fields(projection), None


def _difference_errors(manifest: dict[str, Any]) -> list[str]:
    errors = []
    for item in manifest.get("expected_differences") or []:
        _vector, problem = _revalidate_difference(repo_root(), item)
        if problem:
            errors.append(problem)
    return errors


def _field_pins(reference: dict[str, Any]) -> dict[str, str]:
    """Field values one reference pins. Output roles share one field namespace."""
    projection = reference.get("projection") or {}
    role = reference.get("role")
    pins: dict[str, str] = {}
    if role == "donor-native":
        for key, value in (projection.get("fields") or {}).items():
            pins[f"native.{key}"] = str(value)
    elif role == "new-binding":
        pins["binding.key"] = str(projection["key"])
        pins["binding.subject"] = str(projection["subject"])
        pins["binding.value"] = str(projection["value"])
    elif role == "caller-template":
        for key in TEMPLATE_KEYS:
            pins[f"template.{key}"] = str(projection[key])
    elif role in {"donor-output", "specification"}:
        for key, value in (projection.get("fields") or {}).items():
            pins[str(key)] = str(value)
    return pins


def _pin_conflict_errors(expectation: dict[str, Any]) -> list[str]:
    """Refuse two references that pin different values for one field.

    A later reference must not replace an earlier baseline. An approved
    vector is the only way to name a change, and it is not a second pin.
    """
    seen: dict[str, str] = {}
    errors: list[str] = []
    case = str(expectation.get("case", ""))
    for reference in expectation.get("references") or []:
        for field, value in _field_pins(reference).items():
            previous = seen.get(field)
            if previous is None:
                seen[field] = value
                continue
            if previous == value:
                continue
            errors.append(f"conflicting-pin: {case} field: {field}")
    return errors


def _absence_contradiction_errors(manifest: dict[str, Any]) -> list[str]:
    """Refuse an absence approval that denies a field a reference already pins.

    ``old_present`` false is a frozen old absence. Applying it over a field
    that an independent reference for the same case already contains would
    replace that baseline with an absence pin.
    """
    expectations = {
        item.get("case"): item for item in manifest.get("expectations") or []
    }
    errors: list[str] = []
    for item in manifest.get("expected_differences") or []:
        vector, problem = _revalidate_difference(repo_root(), item)
        if problem or vector is None or vector["old_present"]:
            continue
        expectation = expectations.get(vector["case"])
        if expectation is None:
            continue
        field = vector["field"]
        for reference in expectation.get("references") or []:
            if field in _field_pins(reference):
                errors.append(f"contradictory-absence: {vector['case']} field: {field}")
                break
    return errors


def _bound_selectors(expectation: dict[str, Any], row_id: str) -> dict[str, Any]:
    """Selectors for one row: case selectors, then that row's own, then references.

    A case that exercises several rows keeps the shared selectors on the case
    and the fields that differ, such as valueType, on each row binding.
    Reference projections are applied before the row binding so the row's own
    recorded selectors distinguish rows that share one vector.
    """
    selectors: dict[str, Any] = dict(expectation.get("selectors") or {})
    for reference in expectation.get("references") or []:
        projection = reference.get("projection") or {}
        if isinstance(projection, dict) and isinstance(projection.get("selectors"), dict):
            selectors.update(projection["selectors"])
    for bound in expectation.get("rows") or []:
        if bound.get("row") == row_id and isinstance(bound.get("selectors"), dict):
            selectors.update(bound["selectors"])
    return selectors


def _inputs(value: dict[str, Any]) -> dict[str, str]:
    qualifiers = value.get("qualifiers") or []
    if isinstance(qualifiers, list):
        rendered = ",".join(str(item) for item in qualifiers)
    else:
        rendered = str(qualifiers)
    return {
        "raw": "" if value.get("raw") is None else str(value.get("raw")),
        "qualifiers": rendered,
        "clock": "" if value.get("clock") is None else str(value.get("clock")),
        "state": "" if value.get("state") is None else str(value.get("state")),
    }


def _seal(repositories: dict[str, list[str]], donor_sha: str) -> list[dict[str, Any]]:
    entries = []
    for repository in repositories:
        payload = list_bytes(repositories[repository])
        entries.append({
            "repository": repository,
            "paths": [] if not payload else payload.decode().splitlines(),
            "sha256": digest(payload),
            "donor_sha": donor_sha,
        })
    return entries


def _write_lists(directory: Path, row: str, entries: list[dict[str, Any]]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        payload = list_bytes(entry["paths"])
        path = directory / f"{row}.{entry['repository']}.lst"
        path.write_bytes(payload)


def _account_tests(
    tests: list[Any],
    moved_names: set[str],
    outside_names: set[str],
    spec: dict[str, Any],
    stays: list[dict[str, Any]],
    assertion_records: list[dict[str, Any]],
    seen: set[tuple[str, str]],
    errors: list[str],
) -> None:
    supplied = {
        (item["function"], item["name"]): item
        for item in spec.get("assertions") or []
    }
    specimens = set(spec.get("specimens") or [])
    for test in tests:
        kind = closure.classify_test(test, moved_names, outside_names)
        if kind == "unrelated":
            continue
        if test.name in specimens:
            stays.append({
                "kind": "specimen",
                "name": test.name,
                "file": test.file,
                "function": test.name,
            })
            continue
        if kind == "only-moved":
            errors.append(f"left-behind: {test.name}")
            continue
        moved_only = []
        staying = []
        for assertion in test.assertions:
            uses_moved = bool(assertion.uses & moved_names)
            uses_stay = bool(assertion.uses & outside_names)
            if uses_moved and not uses_stay:
                moved_only.append(assertion)
            else:
                staying.append(assertion)
        if not moved_only:
            stays.append({
                "kind": "test",
                "name": test.name,
                "file": test.file,
                "function": test.name,
            })
            continue
        for assertion in staying:
            stays.append({
                "kind": "assertion",
                "name": assertion.name,
                "file": assertion.file,
                "function": assertion.function,
            })
        for assertion in moved_only:
            key = (assertion.function, assertion.name)
            seen.add(key)
            given = supplied.get(key)
            if given is None or not given.get("test") or not given.get("destination_path"):
                errors.append(
                    "unaccounted-assertion "
                    f"function={assertion.function} assertion={assertion.name}"
                )
                continue
            assertion_records.append({
                "name": assertion.name,
                "file": assertion.file,
                "function": assertion.function,
                "helpers": assertion.helpers,
                "destination_repository": given["destination_repository"],
                "destination_path": given["destination_path"],
                "test": given["test"],
            })


def _accounting(donor: Path, spec: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    errors: list[str] = []
    symbol_level = bool(spec.get("symbol_moves"))
    if symbol_level and spec.get("moves"):
        return {}, ["moves-and-symbol-moves"]
    moves = spec.get("moves") or []
    moved_paths = [item["path"] for item in moves]
    moved_paths += sorted({item["path"] for item in spec.get("symbol_moves") or []})
    for item in spec.get("shared") or []:
        if item["repository"] == spec["donor_repository"]:
            if not gitstore.path_exists(donor, spec["donor_sha"], item["path"]):
                errors.append(f"absent: {item['path']}")
    for path in moved_paths:
        if not gitstore.path_exists(donor, spec["donor_sha"], path):
            errors.append(f"absent: {path}")
    if errors:
        return {}, errors
    stays: list[dict[str, Any]] = []
    assertion_records: list[dict[str, Any]] = []
    symbols: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    if symbol_level:
        symbol_facts = closure.analyze_symbols(
            donor, spec["donor_sha"], spec["symbol_moves"], spec.get("stay_symbols") or []
        )
        if symbol_facts.errors:
            return {}, symbol_facts.errors
        for name in symbol_facts.outside_uses:
            errors.append(f"outside-set: {name}")
        if errors:
            return {}, errors
        symbols = [
            {
                "name": item["name"],
                "file": item["file"],
                "uses": item["uses"],
                "package": item["package"],
            }
            for item in symbol_facts.moved
        ]
        for directory in sorted(symbol_facts.tests):
            _account_tests(
                symbol_facts.tests[directory],
                symbol_facts.moved_names[directory],
                symbol_facts.outside_names[directory],
                spec, stays, assertion_records, seen, errors,
            )
        for item in symbol_facts.stays:
            stays.append({
                "kind": "symbol",
                "name": item["name"],
                "file": item["file"],
                "package": item["package"],
            })
    elif moved_paths:
        try:
            facts = closure.analyze(donor, spec["donor_sha"], moved_paths)
        except ValueError as error:
            return {}, [str(error)]
        for name in facts.outside_uses:
            errors.append(f"outside-set: {name}")
        if facts.outside_uses:
            return {}, errors
        for name in sorted(facts.moved_decls):
            symbols.append({
                "name": name,
                "file": facts.moved_decls[name],
                "uses": facts.symbol_uses.get(name, []),
            })
        _account_tests(
            facts.tests, set(facts.moved_decls), set(facts.outside_decls),
            spec, stays, assertion_records, seen, errors,
        )
    if moved_paths:
        for item in spec.get("assertions") or []:
            key = (item["function"], item["name"])
            if key not in seen:
                errors.append(f"unknown-assertion function={key[0]} assertion={key[1]}")
    if errors:
        return {}, errors
    return {
        "symbols": symbols,
        "assertions": assertion_records,
        "stays": stays,
    }, []


def _pattern_records(donor: Path, tool: Path, spec: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
    errors: list[str] = []
    expectations_in = spec.get("expectations") or []
    recorded_expectations: list[dict[str, Any]] = []
    for item in expectations_in:
        references = []
        for reference in item.get("references") or []:
            try:
                references.append(_record_reference(tool, reference))
            except KeyError as error:
                errors.append(str(error))
            except ValueError as error:
                errors.append(str(error))
        recorded_rows = []
        for bound in item.get("rows") or []:
            recorded_row = {"row": bound.get("row"), "assertion": bound.get("assertion")}
            if bound.get("selectors"):
                recorded_row["selectors"] = bound["selectors"]
            recorded_rows.append(recorded_row)
        recorded_expectations.append({
            "case": item["case"],
            "kind": item["kind"],
            "rows": recorded_rows,
            "inputs": _inputs(item.get("inputs") or {}),
            "selectors": item.get("selectors") or {},
            "references": references,
        })
        errors.extend(_pin_conflict_errors(recorded_expectations[-1]))
    differences = []
    for item in spec.get("expected_differences") or []:
        if item.get("old") == "*" or item.get("new") == "*":
            errors.append("wildcard-difference")
            continue
        if not item.get("source") or not item.get("approval"):
            errors.append("missing-approval")
            continue
        reference = {
            "role": "expected-difference",
            "repository": item["repository"],
            "revision": item["revision"],
            "path": item["path"],
        }
        try:
            recorded = _record_reference(tool, reference)
        except (KeyError, ValueError) as error:
            errors.append(str(error))
            continue
        projection = recorded["projection"]
        entry = {
            "case": item["case"],
            "field": item["field"],
            "old_present": bool(item.get("old_present", True)),
            "old": item.get("old"),
            "new": item.get("new"),
            "source": item["source"],
            "approval": item["approval"],
            "reference": recorded,
        }
        if not _difference_agrees(entry, projection):
            errors.append(f"mutated: {item['repository']}:{item['path']}")
        differences.append(entry)
    by_case = {item["case"]: item for item in recorded_expectations}
    pattern_records = []
    for row in spec.get("mapping_rows") or []:
        row_id = row["row"]
        kind = row["kind"]
        if kind not in MAPPING_KINDS:
            errors.append(f"unsupported-kind: {kind}")
            continue
        cases = row.get("cases") or []
        assertion = row.get("assertion") or ""
        if not cases or not assertion:
            errors.append(f"row: {row_id}")
            continue
        for case in cases:
            expectation = by_case.get(case)
            if expectation is None:
                errors.append(f"row: {row_id}")
                continue
            paired = {"row": row_id, "assertion": assertion}
            if paired not in expectation["rows"] and paired not in [
                {"row": item.get("row"), "assertion": item.get("assertion")}
                for item in expectation["rows"]
            ]:
                errors.append(f"row: {row_id}")
        if kind == "donor-backed":
            if not row.get("old_symbol") or not row.get("bom_entry"):
                errors.append(f"row: {row_id}")
            for case in cases:
                expectation = by_case.get(case)
                if expectation is None:
                    continue
                roles = {item["role"] for item in expectation["references"]}
                if "donor-output" not in roles:
                    errors.append(f"donor-output: {row_id}")
        if kind == "specification":
            if row.get("old_symbol") or row.get("bom_entry"):
                errors.append(f"invented-donor: {row_id}")
            for case in cases:
                expectation = by_case.get(case)
                if expectation is None:
                    continue
                roles = {item["role"] for item in expectation["references"]}
                if "donor-output" in roles or "donor-native" in roles:
                    errors.append(f"invented-donor: {row_id}")
                if "specification" not in roles:
                    errors.append(f"row: {row_id}")
        if kind == "binding":
            for case in cases:
                expectation = by_case.get(case)
                if expectation is None:
                    continue
                roles = {item["role"] for item in expectation["references"]}
                for role in BINDING_ROLES:
                    if role not in roles:
                        errors.append(f"binding-operand: {role}")
                if "donor-output" in roles:
                    errors.append(f"invented-donor: {row_id}")
        signature = row["signature"]
        exemplar = row["exemplar"]
        try:
            blob = _blob(donor, exemplar["revision"], exemplar["path"])
        except KeyError:
            errors.append(
                f"unavailable: {exemplar['repository']}:{exemplar['path']}"
            )
            errors.append(f"row: {row_id}")
            continue
        try:
            rows = patternlib.parse_rows(blob)
        except (json.JSONDecodeError, ValueError) as error:
            errors.append(f"row: {row_id}")
            errors.append(str(error))
            continue
        if not any(patternlib.same_signature(item.get("signature"), signature) for item in rows):
            errors.append(f"signature-mismatch row: {row_id}")
            continue
        candidate = row["candidate"]
        operands = dict(candidate.get("operands") or {})
        if candidate.get("form") == "reference":
            reference = {
                "role": "candidate",
                "repository": candidate["repository"],
                "revision": candidate["revision"],
                "path": candidate["path"],
            }
            try:
                recorded = _record_reference(tool, reference)
            except KeyError:
                errors.append(
                    "candidate-reference: "
                    f"{candidate['repository']} {candidate['path']} {candidate.get('row_key', '')}"
                )
                errors.append(f"row: {row_id}")
                continue
            except ValueError as error:
                errors.append(str(error))
                continue
            projection = recorded["projection"]
            rows_map = projection.get("rows") or {}
            selected = rows_map.get(candidate["row_key"])
            if not isinstance(selected, dict):
                errors.append(
                    "candidate-reference: "
                    f"{candidate['repository']} {candidate['path']} {candidate['row_key']}"
                )
                errors.append(f"row: {row_id}")
                continue
            operands = dict(selected.get("operands") or {})
            candidate = {
                "form": "reference",
                "repository": candidate["repository"],
                "revision": candidate["revision"],
                "path": candidate["path"],
                "row_key": candidate["row_key"],
                "reference": recorded,
                "operands": operands,
            }
        else:
            candidate = {"form": "inline", "operands": operands}
        problem = patternlib.operand_problem(signature, operands)
        if problem:
            errors.append(f"{problem} row: {row_id}")
        selectors: dict[str, Any] = {}
        for case in cases:
            expectation = by_case.get(case)
            if expectation is None:
                continue
            selectors.update(_bound_selectors(expectation, row_id))
        missing = patternlib.selector_problem(signature, operands, selectors)
        if missing:
            errors.append(f"selector-mismatch row: {row_id} field: {missing}")
        pattern_records.append({
            "row": row_id,
            "kind": kind,
            "old_symbol": row.get("old_symbol") or "",
            "bom_entry": row.get("bom_entry") or "",
            "cases": list(cases),
            "assertion": assertion,
            "signature": signature,
            "candidate": candidate,
            "exemplar": {
                "repository": exemplar["repository"],
                "path": exemplar["path"],
                "revision": exemplar["revision"],
            },
        })
    return pattern_records, recorded_expectations, differences, errors


def _destinations(spec: dict[str, Any], accounted: dict[str, Any], patterns: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    moves_by_path = {item["path"]: item for item in spec.get("moves") or []}
    symbol_moves = {
        (item["package"].rstrip("/"), item["path"], item["symbol"]): item
        for item in spec.get("symbol_moves") or []
    }
    for symbol in accounted.get("symbols") or []:
        if "package" in symbol:
            move = symbol_moves[(symbol["package"], symbol["file"], symbol["name"])]
            entries.append({
                "kind": "symbol",
                "name": symbol["name"],
                "package": symbol["package"],
                "repository": move["destination_repository"],
                "path": move["destination_path"],
                "destination_name": move.get("destination_symbol") or symbol["name"],
            })
            continue
        move = moves_by_path[symbol["file"]]
        entries.append({
            "kind": "symbol",
            "name": symbol["name"],
            "repository": move["destination_repository"],
            "path": move["destination_path"],
        })
    for assertion in accounted.get("assertions") or []:
        entries.append({
            "kind": "assertion",
            "name": assertion["name"],
            "function": assertion["function"],
            "repository": assertion["destination_repository"],
            "path": assertion["destination_path"],
            "test": assertion["test"],
        })
    expectations = {item["case"]: item for item in spec.get("expectations") or []}
    for pattern in patterns:
        for case in pattern["cases"]:
            expectation = expectations[case]
            destination = None
            for item in spec.get("expectations") or []:
                if item["case"] != case:
                    continue
                for row in item.get("rows") or []:
                    if row.get("row") == pattern["row"] and row.get("assertion") == pattern["assertion"]:
                        destination = row.get("destination") or item.get("destination")
            if destination is None or not destination.get("test"):
                raise ValueError(f"row: {pattern['row']}")
            entries.append({
                "kind": "case",
                "case": case,
                "row": pattern["row"],
                "assertion": pattern["assertion"],
                "repository": destination["repository"],
                "path": destination["path"],
                "test": destination["test"],
            })
    return entries


def _repositories(spec: dict[str, Any]) -> dict[str, list[str]]:
    donor_name = spec["donor_repository"]
    grouped: dict[str, list[str]] = {donor_name: []}
    for move in spec.get("moves") or []:
        grouped[donor_name].append(move["path"])
        grouped.setdefault(move["destination_repository"], []).append(move["destination_path"])
    for move in spec.get("symbol_moves") or []:
        grouped[donor_name].append(move["path"])
        grouped.setdefault(move["destination_repository"], []).append(move["destination_path"])
    for item in spec.get("new_files") or []:
        grouped.setdefault(item["repository"], []).append(item["path"])
    for item in spec.get("shared") or []:
        grouped.setdefault(item["repository"], []).append(item["path"])
    for item in spec.get("expectations") or []:
        for row in item.get("rows") or []:
            destination = row.get("destination") or item.get("destination")
            if destination:
                grouped.setdefault(destination["repository"], []).append(destination["path"])
    return grouped


def build_manifest(donor: Path, tool: Path, spec: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    if not gitstore.commit_exists(donor, spec["donor_sha"]):
        return None, [f"unavailable: {spec['donor_sha']}:"]
    accounted, errors = _accounting(donor, spec)
    pattern_records, expectations, differences, pattern_errors = _pattern_records(donor, tool, spec)
    errors.extend(pattern_errors)
    if errors:
        return None, errors
    try:
        destinations = _destinations(spec, accounted, pattern_records)
    except ValueError as error:
        return None, [str(error)]
    grouped = _repositories(spec)
    manifest = {
        "row": spec["row"],
        "donor": {"repository": spec["donor_repository"], "sha": spec["donor_sha"]},
        "paths": _seal(grouped, spec["donor_sha"]),
        "symbols": accounted.get("symbols") or [],
        "assertions": accounted.get("assertions") or [],
        "stays": accounted.get("stays") or [],
        "patterns": pattern_records,
        "destinations": destinations,
        "expectations": expectations,
        "expected_differences": differences,
        "receipts": [],
    }
    contradiction = _absence_contradiction_errors(manifest)
    if contradiction:
        return None, contradiction
    return manifest, []


def generate(spec: dict[str, Any], donor: Path) -> int:
    manifest, errors = build_manifest(donor, repo_root(), spec)
    if errors or manifest is None:
        return emit(errors or ["generate-failed"])
    directory = manifest_dir()
    directory.mkdir(parents=True, exist_ok=True)
    _write_lists(directory, manifest["row"], manifest["paths"])
    target = directory / f"{manifest['row']}.json"
    target.write_text(dump(manifest), encoding="utf-8")
    import sys
    sys.stdout.write(dump(manifest))
    return 0


def _list_problem(manifest_path: Path, manifest: dict[str, Any]) -> list[str]:
    errors = []
    for entry in manifest["paths"]:
        payload = list_bytes(entry["paths"])
        if digest(payload) != entry["sha256"]:
            errors.append(f"sealed-hash: {entry['repository']}")
        if entry.get("donor_sha") != manifest["donor"]["sha"]:
            errors.append(f"sealed-donor: {entry['repository']}")
        sibling = manifest_path.parent / f"{manifest['row']}.{entry['repository']}.lst"
        if not sibling.is_file() or sibling.read_bytes() != payload:
            errors.append(f"sealed-list: {entry['repository']}")
    return errors


def _binding_problems(manifest: dict[str, Any]) -> list[str]:
    errors = []
    expectations = {item["case"]: item for item in manifest["expectations"]}
    for pattern in manifest["patterns"]:
        kind = pattern.get("kind")
        if kind not in MAPPING_KINDS:
            errors.append(f"unsupported-kind: {kind}")
            continue
        if not pattern.get("cases") or not pattern.get("assertion"):
            errors.append(f"row: {pattern['row']}")
            continue
        for case in pattern["cases"]:
            expectation = expectations.get(case)
            if expectation is None:
                errors.append(f"row: {pattern['row']}")
                continue
            wanted = {"row": pattern["row"], "assertion": pattern["assertion"]}
            actual = [
                {"row": item.get("row"), "assertion": item.get("assertion")}
                for item in expectation.get("rows") or []
            ]
            if wanted not in actual:
                errors.append(f"row: {pattern['row']}")
        roles: set[str] = set()
        for case in pattern["cases"]:
            expectation = expectations.get(case)
            if expectation is None:
                continue
            roles.update(item["role"] for item in expectation.get("references") or [])
        if kind == "binding":
            for role in BINDING_ROLES:
                if role not in roles:
                    errors.append(f"binding-operand: {role}")
        if kind == "donor-backed" and "donor-output" not in roles:
            errors.append(f"donor-output: {pattern['row']}")
        if kind == "specification" and (pattern.get("old_symbol") or pattern.get("bom_entry")):
            errors.append(f"invented-donor: {pattern['row']}")
    return errors


def _pattern_check(donor: Path, tool: Path, manifest: dict[str, Any]) -> list[str]:
    errors = []
    expectations = {item["case"]: item for item in manifest["expectations"]}
    for pattern in manifest["patterns"]:
        row_id = pattern["row"]
        exemplar = pattern["exemplar"]
        try:
            blob = _blob(donor, exemplar["revision"], exemplar["path"])
        except KeyError:
            errors.append(f"unavailable: {exemplar['repository']}:{exemplar['path']}")
            errors.append(f"row: {row_id}")
            continue
        try:
            rows = patternlib.parse_rows(blob)
        except (json.JSONDecodeError, ValueError):
            errors.append(f"signature-mismatch row: {row_id}")
            continue
        if not any(patternlib.same_signature(item.get("signature"), pattern["signature"]) for item in rows):
            errors.append(f"signature-mismatch row: {row_id}")
            continue
        candidate = pattern["candidate"]
        operands = dict(candidate.get("operands") or {})
        if candidate.get("form") == "reference":
            projection, problem = _reload_reference(tool, candidate["reference"])
            if problem or projection is None:
                errors.append(problem or "candidate-reference")
                errors.append(
                    "candidate-reference: "
                    f"{candidate['repository']} {candidate['path']} {candidate.get('row_key', '')}"
                )
                errors.append(f"row: {row_id}")
                continue
            selected = (projection.get("rows") or {}).get(candidate["row_key"])
            if not isinstance(selected, dict):
                errors.append(
                    "candidate-reference: "
                    f"{candidate['repository']} {candidate['path']} {candidate['row_key']}"
                )
                errors.append(f"row: {row_id}")
                continue
            operands = dict(selected.get("operands") or {})
            if patternlib.canonical(operands) != patternlib.canonical(candidate.get("operands")):
                errors.append(f"selector-mismatch row: {row_id}")
        problem = patternlib.operand_problem(pattern["signature"], operands)
        if problem:
            errors.append(f"{problem} row: {row_id}")
        selectors: dict[str, Any] = {}
        for case in pattern["cases"]:
            expectation = expectations.get(case)
            if expectation is None:
                errors.append(f"row: {row_id}")
                continue
            reloaded_expectation = {
                "selectors": expectation.get("selectors") or {},
                "rows": expectation.get("rows") or [],
                "references": [],
            }
            for reference in expectation.get("references") or []:
                reloaded, reference_problem = _reload_reference(tool, reference)
                if reference_problem or reloaded is None:
                    errors.append(reference_problem or f"unavailable: {reference['path']}")
                    continue
                reloaded_expectation["references"].append({"projection": reloaded})
            selectors.update(_bound_selectors(reloaded_expectation, row_id))
        missing = patternlib.selector_problem(pattern["signature"], operands, selectors)
        if missing:
            errors.append(f"selector-mismatch row: {row_id} field: {missing}")
    for expectation in manifest["expectations"]:
        errors.extend(_pin_conflict_errors(expectation))
        for reference in expectation.get("references") or []:
            _reloaded, problem = _reload_reference(tool, reference)
            if problem:
                errors.append(problem)
    for difference in manifest["expected_differences"]:
        recorded = difference.get("reference") or {}
        reloaded, problem = _reload_reference(tool, difference["reference"])
        if problem or reloaded is None:
            errors.append(
                problem or f"mutated: {recorded.get('repository', '')}:{recorded.get('path', '')}"
            )
            continue
        if not _difference_agrees(difference, reloaded):
            errors.append(f"mutated: {recorded.get('repository', '')}:{recorded.get('path', '')}")
    errors.extend(_absence_contradiction_errors(manifest))
    return errors


def _closure_check(donor: Path, manifest: dict[str, Any]) -> list[str]:
    errors = []
    if gitstore.head_sha(donor) != manifest["donor"]["sha"]:
        errors.append("donor-sha")
        return errors
    donor_entry = next(
        (item for item in manifest["paths"] if item["repository"] == manifest["donor"]["repository"]),
        None,
    )
    moved = sorted({item["file"] for item in manifest["symbols"]})
    for path in moved:
        if not gitstore.path_exists(donor, manifest["donor"]["sha"], path):
            errors.append(f"absent: {path}")
    if donor_entry:
        for path in donor_entry["paths"]:
            if not gitstore.path_exists(donor, manifest["donor"]["sha"], path):
                errors.append(f"absent: {path}")
    if errors:
        return errors
    if not moved:
        return errors
    symbol_level = any("package" in item for item in manifest["symbols"])
    symbol_moves: list[dict[str, Any]] = []
    if symbol_level:
        for item in manifest["symbols"]:
            destination = [
                entry for entry in manifest["destinations"]
                if entry.get("kind") == "symbol"
                and entry.get("package") == item.get("package")
                and entry.get("name") == item["name"]
            ]
            if len(destination) != 1 or any(
                not _text_present(destination[0].get(key))
                for key in ("repository", "path", "destination_name")
            ):
                errors.append(f"missing-destination symbol={item.get('package')}:{item['name']}")
                continue
            symbol_moves.append({
                "package": item["package"],
                "path": item["file"],
                "symbol": item["name"],
                "destination_repository": destination[0]["repository"],
                "destination_path": destination[0]["path"],
                "destination_symbol": destination[0]["destination_name"],
            })
        if errors:
            return errors
    else:
        try:
            facts = closure.analyze(donor, manifest["donor"]["sha"], moved)
        except ValueError as error:
            return [str(error)]
        for name in facts.outside_uses:
            errors.append(f"outside-set: {name}")
        if facts.outside_uses:
            return errors
        expected_symbols = {item["name"] for item in manifest["symbols"]}
        if expected_symbols != set(facts.moved_decls):
            errors.append("symbol-set")
    specimens = [
        item["name"] for item in manifest["stays"] if item.get("kind") == "specimen"
    ]
    supplied = []
    for item in manifest["assertions"]:
        destination = next(
            (
                entry for entry in manifest["destinations"]
                if entry.get("kind") == "assertion"
                and entry.get("function") == item["function"]
                and entry.get("name") == item["name"]
            ),
            None,
        )
        supplied.append({
            "function": item["function"],
            "name": item["name"],
            "test": None if destination is None else destination.get("test"),
            "destination_path": None if destination is None else destination.get("path"),
            "destination_repository": None if destination is None else destination.get("repository"),
        })
    spec = {
        "donor_repository": manifest["donor"]["repository"],
        "donor_sha": manifest["donor"]["sha"],
        "moves": [] if symbol_level else [{"path": path} for path in moved],
        "symbol_moves": symbol_moves,
        "stay_symbols": [
            {"package": item["package"], "path": item["file"], "symbol": item["name"]}
            for item in manifest["stays"] if item.get("kind") == "symbol"
        ],
        "assertions": supplied,
        "specimens": specimens,
        "shared": [],
    }
    recomputed, account_errors = _accounting(donor, spec)
    errors.extend(account_errors)
    if account_errors or not recomputed:
        return errors
    def stays_key(item: dict[str, Any]) -> tuple[str, str, str, str, str]:
        return (
            item.get("kind", ""), item.get("function", ""), item.get("name", ""),
            item.get("package", ""), item.get("file", ""),
        )
    if sorted(recomputed["stays"], key=stays_key) != sorted(manifest["stays"], key=stays_key):
        errors.append("stays")
    recomputed_assertions = [
        (item["function"], item["name"], item["helpers"]) for item in recomputed["assertions"]
    ]
    manifest_assertions = [
        (item["function"], item["name"], item["helpers"]) for item in manifest["assertions"]
    ]
    if sorted(recomputed_assertions) != sorted(manifest_assertions):
        errors.append("assertions")
    if symbol_level and recomputed["symbols"] != manifest["symbols"]:
        errors.append("symbol-set")
    return errors


def _text_present(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _case_destination_problems(manifest: dict[str, Any]) -> list[str]:
    """Each bound case needs one destination that names repository, path and test.

    Zero matches, or a match that omits one of those fields, is a missing
    identity. More than one match is ambiguous. The message names the case,
    the row and the assertion.
    """
    errors = []
    destinations = [
        entry for entry in manifest.get("destinations") or []
        if entry.get("kind") == "case"
    ]
    for pattern in manifest.get("patterns") or []:
        row_id = str(pattern.get("row") or "")
        assertion = str(pattern.get("assertion") or "")
        for case in pattern.get("cases") or []:
            matches = [
                entry for entry in destinations
                if entry.get("case") == case
                and entry.get("row") == row_id
                and entry.get("assertion") == assertion
            ]
            identity = f"case={case} row={row_id} assertion={assertion}"
            if len(matches) > 1:
                errors.append(f"ambiguous-destination {identity}")
                continue
            if len(matches) != 1 or any(
                not _text_present(matches[0].get(key))
                for key in ("repository", "path", "test")
            ):
                errors.append(f"missing-destination {identity}")
    return errors


def check(manifest_path: Path, donor: Path) -> int:
    manifest = load_json(manifest_path)
    before = manifest_path.read_bytes()
    errors: list[str] = []
    errors.extend(_list_problem(manifest_path, manifest))
    errors.extend(_closure_check(donor, manifest))
    errors.extend(_binding_problems(manifest))
    errors.extend(_case_destination_problems(manifest))
    errors.extend(_pattern_check(donor, repo_root(), manifest))
    if manifest_path.read_bytes() != before:
        errors.append("check-wrote")
    if errors:
        return emit(errors)
    import sys
    sys.stdout.write("check: ok\n")
    return 0


def _approved(manifest: dict[str, Any], case: str, field: str, old_present: bool, old: Any, new: Any) -> bool:
    for item in manifest.get("expected_differences") or []:
        vector, problem = _revalidate_difference(repo_root(), item)
        if problem or vector is None:
            continue
        if vector["case"] != case or vector["field"] != field:
            continue
        if vector["old_present"] != old_present:
            continue
        if vector["new"] != new:
            continue
        if old_present and vector["old"] != old:
            continue
        return True
    return False


def _case_covers(vector_case: Any, result_case: str) -> bool:
    """A vector covers a result when the cases are equal, or the vector is global.

    ``*`` is the only global case. A vector for one named case does not cover
    a result that names another case.
    """
    return vector_case == "*" or vector_case == result_case


def _status_vector_matches(manifest: dict[str, Any], case: str, old_status: int, new_status: int) -> bool:
    """True when an approved status transition covers this result's case.

    An exact case match is required. A vector whose case is ``*`` is the
    explicit approval for every case. Matching only the old and new status
    does not let one case's approval stand in for another.
    """
    old = str(old_status)
    new = str(new_status)
    if _approved(manifest, case, "execution_status", True, old, new):
        return True
    if case == "*":
        return False
    return _approved(manifest, "*", "execution_status", True, old, new)


def _pins(manifest: dict[str, Any], expectation: dict[str, Any]) -> dict[str, dict[str, Any]]:
    pins: dict[str, dict[str, Any]] = {}
    kind = expectation["kind"]
    for reference in expectation.get("references") or []:
        for name, value in _field_pins(reference).items():
            proposed = {"present": True, "value": value}
            current = pins.get(name)
            # Keep the first pin when a later reference disagrees. Generation,
            # check and compare reject that manifest before a comparison uses it.
            if current is None or current == proposed:
                pins[name] = proposed
    case = expectation["case"]
    for item in manifest.get("expected_differences") or []:
        vector, problem = _revalidate_difference(repo_root(), item)
        if problem or vector is None or vector["case"] != case:
            continue
        if vector["old_present"]:
            pins.setdefault(vector["field"], {"present": True, "value": str(vector.get("old"))})
        elif vector["field"] not in pins:
            # Absence names a field the references do not pin. It must not
            # replace a baseline those references already recorded.
            pins[vector["field"]] = {"present": False, "value": "absent"}
    if kind == "binding":
        for key in ("binding.key", "binding.subject", "binding.value"):
            pins.setdefault(key, {"present": True, "value": ""})
    return pins


def _parse_marked(output: str, prefix: str) -> list[dict[str, str]]:
    found = []
    for line in output.splitlines():
        if prefix not in line:
            continue
        payload = line[line.index(prefix) + len(prefix):].strip()
        item = {}
        for part in payload.split():
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            item[key] = value
        if item:
            found.append(item)
    return found


def _run_case(
    destination: Path,
    entry: dict[str, Any],
    expectation: dict[str, Any],
    manifest: dict[str, Any],
) -> list[str]:
    case = entry["case"]
    row = entry["row"]
    assertion = entry["assertion"]
    test = entry["test"]
    identity = f"case={case} row={row} assertion={assertion} test={test}"
    package = str(Path(entry["path"]).parent)
    target = "." if package in ("", ".") else "./" + package
    pins = _pins(manifest, expectation)
    environment = os.environ.copy()
    environment.update({
        "GOWORK": "off",
        "GOFLAGS": "-mod=mod",
        "GOPROXY": "off",
        "GOSUMDB": "off",
        "GO111MODULE": "on",
        "MANIFEST_CASE": case,
        "MANIFEST_ROW": row,
        "MANIFEST_ASSERTION": assertion,
        "MANIFEST_RAW": expectation["inputs"].get("raw", ""),
        "MANIFEST_QUALIFIERS": expectation["inputs"].get("qualifiers", ""),
        "MANIFEST_CLOCK": expectation["inputs"].get("clock", ""),
        "MANIFEST_STATE": expectation["inputs"].get("state", ""),
    })
    template = {
        key: pins[f"template.{key}"]["value"]
        for key in TEMPLATE_KEYS
        if f"template.{key}" in pins
    }
    for key, env_key in (
        ("origin", "MANIFEST_ORIGIN"),
        ("quality", "MANIFEST_QUALITY"),
        ("source", "MANIFEST_SOURCE"),
        ("timing", "MANIFEST_TIMING"),
        ("provenance", "MANIFEST_PROVENANCE"),
    ):
        environment[env_key] = template.get(key, "")
    environment["MANIFEST_PINNED_FIELDS"] = json.dumps(
        {key: value["value"] for key, value in pins.items()},
        sort_keys=True,
    )
    completed = subprocess.run(
        ["go", "test", "-count=1", "-v", "-run", f"^{test}$", target],
        cwd=str(destination),
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )
    output = completed.stdout + "\n" + completed.stderr
    passed_marker = f"--- PASS: {test}"
    failed_marker = f"--- FAIL: {test}"
    messages = [
        f"outcome assertion={assertion} test={test} invocation-status={completed.returncode} "
        f"case={case} row={row}"
    ]
    if "no tests to run" in output or (passed_marker not in output and failed_marker not in output):
        messages[0] += " result=fail"
        messages.append(f"not-executed {identity}")
        return messages
    results = _parse_marked(output, "MANIFEST_RESULT ")
    matched = [
        item for item in results
        if item.get("case") == case and item.get("row") == row and item.get("assertion") == assertion
    ]
    if not matched:
        messages[0] += " result=fail"
        messages.append(f"not-executed {identity}")
        return messages
    failed = False
    inputs = _parse_marked(output, "MANIFEST_INPUT ")
    if inputs:
        observed_input = inputs[-1]
        for key in ("raw", "qualifiers", "clock", "state"):
            if observed_input.get(key, "") != expectation["inputs"].get(key, ""):
                messages.append(
                    f"input-mismatch {identity} field={key} "
                    f"expected={expectation['inputs'].get(key, '')} observed={observed_input.get(key, '')}"
                )
                failed = True
    else:
        messages.append(f"input-mismatch {identity}")
        failed = True
    metas = _parse_marked(output, "MANIFEST_META ")
    if template:
        if not metas:
            messages.append(f"template-mismatch {identity}")
            failed = True
        else:
            meta = metas[-1]
            for key in TEMPLATE_KEYS:
                if meta.get(key, "") != template[key]:
                    messages.append(
                        f"field assertion={assertion} field=template.{key} "
                        f"expected={template[key]} observed={meta.get(key, '')}"
                    )
                    failed = True
    fields = _parse_marked(output, "MANIFEST_FIELD ")
    by_name = {item.get("field", ""): item for item in fields}
    for name, pin in pins.items():
        if name.startswith("template."):
            continue
        emitted = by_name.get(name)
        display = "absent" if not pin["present"] else pin["value"]
        if emitted is None or "expected" not in emitted or "observed" not in emitted:
            if name.startswith("binding."):
                messages.append(f"unexecuted-binding assertion={assertion}")
            else:
                messages.append(f"missing-field assertion={assertion} field={name}")
            failed = True
            continue
        observed = emitted["observed"]
        messages.append(
            f"field assertion={assertion} field={name} expected={emitted['expected']} observed={observed}"
        )
        if emitted["expected"] != display:
            failed = True
            continue
        if pin["present"] and observed == pin["value"]:
            continue
        if _approved(manifest, case, name, pin["present"], None if not pin["present"] else pin["value"], observed):
            continue
        failed = True
    for name, emitted in by_name.items():
        if name in pins:
            continue
        if emitted.get("expected") != emitted.get("observed"):
            messages.append(
                f"unapproved-difference: {name} assertion={assertion} "
                f"expected={emitted.get('expected', '')} observed={emitted.get('observed', '')}"
            )
            failed = True
    if completed.returncode != 0 and not failed:
        messages.append(f"invocation-failed {identity}")
        failed = True
    messages[0] += " result=fail" if failed or any(line.startswith(("input-mismatch", "not-executed", "template-mismatch", "unexecuted", "missing-field", "unapproved")) for line in messages[1:]) else " result=pass"
    return messages


def _package_target(path: str) -> str:
    package = str(Path(path).parent)
    return "." if package in ("", ".") else "./" + package


def _run_transferred(destination: Path, entry: dict[str, Any], move: str) -> tuple[list[str], bool]:
    """Run one transferred assertion's destination test.

    An empty patterns list does not skip this. The invocation counts as
    executed only when that test runs and its own output names the assertion.
    """
    name = str(entry.get("name") or "")
    test = str(entry.get("test") or "")
    function = str(entry.get("function") or "")
    identity = f"assertion={name} function={function} test={test} row={move}"
    outcome = (
        f"outcome assertion={name} test={test} invocation-status={{status}} "
        f"case= row={move} result=fail"
    )
    if not test or not entry.get("path"):
        return [f"not-executed {identity}"], False
    environment = os.environ.copy()
    environment.update({
        "GOWORK": "off",
        "GOFLAGS": "-mod=mod",
        "GOPROXY": "off",
        "GOSUMDB": "off",
        "GO111MODULE": "on",
        "MANIFEST_CASE": "",
        "MANIFEST_ROW": move,
        "MANIFEST_ASSERTION": name,
        "MANIFEST_FUNCTION": function,
        "MANIFEST_RAW": "",
        "MANIFEST_QUALIFIERS": "",
        "MANIFEST_CLOCK": "",
        "MANIFEST_STATE": "",
        "MANIFEST_ORIGIN": "",
        "MANIFEST_QUALITY": "",
        "MANIFEST_SOURCE": "",
        "MANIFEST_TIMING": "",
        "MANIFEST_PROVENANCE": "",
        "MANIFEST_PINNED_FIELDS": "{}",
    })
    completed = subprocess.run(
        ["go", "test", "-count=1", "-v", "-run", f"^{test}$", _package_target(entry["path"])],
        cwd=str(destination),
        capture_output=True,
        text=True,
        env=environment,
        check=False,
    )
    output = completed.stdout + "\n" + completed.stderr
    passed_marker = f"--- PASS: {test}"
    failed_marker = f"--- FAIL: {test}"
    named = any(
        item.get("assertion") == name
        for item in _parse_marked(output, "MANIFEST_RESULT ")
    )
    ran = "no tests to run" not in output and (passed_marker in output or failed_marker in output)
    if not ran or not named:
        return [outcome.format(status=completed.returncode), f"not-executed {identity}"], False
    if completed.returncode != 0 or failed_marker in output:
        return [outcome.format(status=completed.returncode)], True
    return [
        (
            f"outcome assertion={name} test={test} invocation-status={completed.returncode} "
            f"case= row={move} result=pass"
        ),
    ], True


def compare(manifest_path: Path, destination: Path) -> int:
    manifest = load_json(manifest_path)
    before = manifest_path.read_bytes()
    # compare reads references from the tool checkout and does not require the donor.
    reference_errors = []
    for expectation in manifest["expectations"]:
        reference_errors.extend(_pin_conflict_errors(expectation))
        for reference in expectation.get("references") or []:
            _reloaded, problem = _reload_reference(repo_root(), reference)
            if problem:
                reference_errors.append(problem)
    reference_errors.extend(_difference_errors(manifest))
    reference_errors.extend(_absence_contradiction_errors(manifest))
    reference_errors.extend(_binding_problems(manifest))
    if reference_errors:
        return emit(reference_errors)
    expectations = {item["case"]: item for item in manifest["expectations"]}
    messages: list[str] = []
    ran = False
    # Transferred assertions are destination checks even when patterns is empty.
    # Success requires those checks to have run; zero executions name the move.
    declared = list(manifest.get("assertions") or [])
    executed: set[tuple[str, str]] = set()
    move = str(manifest.get("row") or "")
    for entry in manifest["destinations"]:
        if entry.get("kind") == "assertion":
            lines, did_run = _run_transferred(destination, entry, move)
            messages.extend(lines)
            if did_run:
                executed.add((str(entry.get("function") or ""), str(entry.get("name") or "")))
            continue
        if entry.get("kind") != "case":
            continue
        ran = True
        expectation = expectations.get(entry["case"])
        if expectation is None:
            messages.append(f"row: {entry['row']}")
            continue
        messages.extend(_run_case(destination, entry, expectation, manifest))
    seen_destinations = {
        (str(entry.get("function") or ""), str(entry.get("name") or ""))
        for entry in manifest["destinations"]
        if entry.get("kind") == "assertion"
    }
    for assertion in declared:
        key = (str(assertion.get("function") or ""), str(assertion.get("name") or ""))
        if key in executed or key in seen_destinations:
            continue
        messages.append(
            "not-executed "
            f"assertion={assertion.get('name', '')} function={assertion.get('function', '')} test= row={move}"
        )
    if declared and not executed:
        messages.append(f"not-executed move={move}")
    for pattern in manifest["patterns"]:
        for case in pattern.get("cases") or []:
            found = any(
                item.get("kind") == "case"
                and item.get("case") == case
                and item.get("row") == pattern["row"]
                and item.get("assertion") == pattern["assertion"]
                for item in manifest["destinations"]
            )
            if not found:
                messages.append(
                    "not-executed "
                    f"case={case} row={pattern['row']} assertion={pattern['assertion']} test="
                )
                messages.append(f"row: {pattern['row']}")
    if manifest_path.read_bytes() != before:
        messages.append("compare-wrote")
    failed = any(
        line.endswith("result=fail") or line.startswith((
            "not-executed", "input-mismatch", "unapproved-difference", "row:",
            "unexecuted-binding", "missing-field", "invocation-failed",
            "template-mismatch", "compare-wrote",
        ))
        for line in messages
    )
    if not failed and not ran and not manifest["patterns"] and not declared:
        import sys
        sys.stdout.write("compare: ok\n")
        return 0
    if failed:
        # Keep passing outcomes visible beside the failures.
        return emit(messages) or 1
    import sys
    sys.stdout.write("".join(line + "\n" for line in messages))
    sys.stdout.write("compare: ok\n")
    return 0


def _field_assignment(line: str) -> tuple[str, str] | None:
    if "=" not in line:
        return None
    key, value = line.split("=", 1)
    if not key or key[0].isdigit():
        return None
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_.-")
    if any(character not in allowed for character in key):
        return None
    return key, value


def _output_delta(old: str, new: str) -> tuple[list[dict[str, Any]], bool]:
    """Changed field occurrences, and whether any other bytes differ.

    Each `field=value` line is its own occurrence. A later line does not
    replace an earlier line of the same field.
    """

    def split(text: str) -> tuple[dict[str, list[str]], list[str]]:
        fields: dict[str, list[str]] = {}
        residual: list[str] = []
        for line in text.splitlines():
            assignment = _field_assignment(line)
            if assignment is None:
                residual.append(line)
                continue
            fields.setdefault(assignment[0], []).append(assignment[1])
        return fields, residual

    old_fields, old_residual = split(old)
    new_fields, new_residual = split(new)
    changes: list[dict[str, Any]] = []
    for field in sorted(set(old_fields) | set(new_fields)):
        old_values = old_fields.get(field, [])
        new_values = new_fields.get(field, [])
        shared = min(len(old_values), len(new_values))
        for index in range(shared):
            if old_values[index] == new_values[index]:
                continue
            changes.append({
                "field": field,
                "old_present": True,
                "old": old_values[index],
                "new": new_values[index],
            })
        for value in new_values[shared:]:
            changes.append({
                "field": field,
                "old_present": False,
                "old": None,
                "new": value,
            })
        for value in old_values[shared:]:
            changes.append({
                "field": field,
                "old_present": True,
                "old": value,
                "new": None,
            })
    residual = old_residual != new_residual or (not changes and old != new)
    return changes, residual


def _difference_matches(diff: dict[str, Any], change: dict[str, Any]) -> bool:
    if diff.get("field") != change["field"]:
        return False
    old_present = bool(diff.get("old_present", True))
    if old_present != change["old_present"]:
        return False
    if diff.get("new") != change["new"]:
        return False
    if old_present and diff.get("old") != change["old"]:
        return False
    return True


def _output_errors(manifest: dict[str, Any], record: dict[str, Any]) -> list[str]:
    """Name output changes that the approved vectors do not account for.

    A listed vector accounts for a change only when its case covers the result
    case, the old and new outputs differ by that field's `field=value` line,
    and the vector names the same old presence, old value and new value.
    ``*`` is the only case that covers a different result. Any other byte
    change is unapproved, including when another approved vector such as
    execution_status is present.
    """
    old = record.get("old_output", "")
    new = record.get("new_output", "")
    if old is None:
        old = ""
    if new is None:
        new = ""
    if old == new:
        return []
    changes, residual = _output_delta(str(old), str(new))
    errors: list[str] = []
    if residual:
        errors.append("unapproved-difference: output")
    result_case = str(record.get("case") or "*")
    differences = list(record.get("differences") or [])
    used = [False] * len(differences)
    for change in changes:
        match_at = None
        for index, diff in enumerate(differences):
            if used[index] or not _difference_matches(diff, change):
                continue
            vector_case = diff.get("case", result_case)
            if not _case_covers(vector_case, result_case):
                continue
            if not _approved(
                manifest,
                vector_case,
                change["field"],
                change["old_present"],
                change["old"],
                change["new"],
            ):
                continue
            match_at = index
            break
        if match_at is None:
            errors.append(f"unapproved-difference: {change['field']}")
        else:
            used[match_at] = True
    return errors


def _judge_receipt(manifest: dict[str, Any], result: dict[str, Any]) -> list[str]:
    errors = []
    errors.extend(_difference_errors(manifest))
    if result["tested_donor_sha"] != manifest["donor"]["sha"]:
        errors.append("donor-sha")
    if result["tested_destination_commit"] != result["commit"]:
        errors.append("destination-commit")
    old_status = int(result["old_status"])
    new_status = int(result["new_status"])
    result_case = str(result.get("case", "*"))
    if old_status != new_status and not _status_vector_matches(
        manifest, result_case, old_status, new_status
    ):
        errors.append("unapproved-difference: execution_status")
    differences = result.get("differences") or []
    for diff in differences:
        if not _case_covers(diff.get("case"), result_case):
            errors.append(f"unapproved-difference: {diff['field']}")
            continue
        old_present = bool(diff.get("old_present", True))
        if not _approved(
            manifest,
            diff["case"],
            diff["field"],
            old_present,
            diff.get("old"),
            diff.get("new"),
        ):
            errors.append(f"unapproved-difference: {diff['field']}")
    errors.extend(_output_errors(manifest, result))
    return errors


def receipt(manifest_path: Path, result: dict[str, Any], checkouts: dict[str, Path]) -> int:
    manifest = load_json(manifest_path)
    original = manifest_path.read_bytes()
    errors = _judge_receipt(manifest, result)
    repository = result["repository"]
    if repository not in _destination_repositories(manifest):
        errors.append(f"not-destination: {repository}")
    checkout = checkouts.get(repository)
    if checkout is None:
        errors.append(f"checkout: {repository}")
    else:
        commit = result["tested_destination_commit"]
        for entry in manifest["destinations"]:
            if entry["repository"] != repository:
                continue
            if not gitstore.path_exists(checkout, commit, entry["path"]):
                errors.append(f"absent: {entry['path']}")
    if result["kind"] == "whole-session":
        for existing in manifest.get("receipts") or []:
            if (
                existing.get("kind") == "row"
                and existing.get("repository") == repository
                and existing.get("destination_commit") == result["commit"]
            ):
                errors.append("destination-commit")
    if result["kind"] == "standalone-classifier":
        compared = set(result.get("compared") or [])
        for surface in CLASSIFIER_SURFACES:
            if surface not in compared:
                errors.append(f"classifier-surface: {surface}")
    if errors:
        if manifest_path.read_bytes() != original:
            errors.append("receipt-wrote")
        return emit(errors)
    entry = {
        "repository": repository,
        "kind": result["kind"],
        "case": str(result.get("case", "*")),
        "donor_sha": result["tested_donor_sha"],
        "destination_commit": result["tested_destination_commit"],
        "old_status": int(result["old_status"]),
        "new_status": int(result["new_status"]),
        "old_output": result.get("old_output", ""),
        "new_output": result.get("new_output", ""),
        "differences": result.get("differences") or [],
        "compared": result.get("compared") or [],
        "outcome": "approved-difference" if result.get("differences") or result.get("old_output") != result.get("new_output") or int(result["old_status"]) != int(result["new_status"]) else "equal",
    }
    manifest["receipts"] = list(manifest.get("receipts") or []) + [entry]
    manifest_path.write_text(dump(manifest), encoding="utf-8")
    import sys
    sys.stdout.write(dump(entry))
    return 0


def _receipt_ok(receipt_entry: dict[str, Any], manifest: dict[str, Any]) -> bool:
    if _difference_errors(manifest):
        return False
    if receipt_entry.get("donor_sha") != manifest["donor"]["sha"]:
        return False
    if receipt_entry.get("destination_commit") in ("", None):
        return False
    if receipt_entry.get("outcome") not in {"equal", "approved-difference"}:
        return False
    result_case = str(receipt_entry.get("case") or "*")
    if int(receipt_entry["old_status"]) != int(receipt_entry["new_status"]):
        if not _status_vector_matches(
            manifest,
            result_case,
            int(receipt_entry["old_status"]),
            int(receipt_entry["new_status"]),
        ):
            return False
        listed = [
            item for item in receipt_entry.get("differences") or []
            if item.get("field") == "execution_status" and _case_covers(item.get("case"), result_case)
        ]
        if not listed:
            return False
    for diff in receipt_entry.get("differences") or []:
        if not _case_covers(diff.get("case"), result_case):
            return False
        if not _approved(
            manifest,
            diff["case"],
            diff["field"],
            bool(diff.get("old_present", True)),
            diff.get("old"),
            diff.get("new"),
        ):
            return False
    if _output_errors(manifest, receipt_entry):
        return False
    return True


def _destination_repositories(manifest: dict[str, Any]) -> set[str]:
    donor = (manifest.get("donor") or {}).get("repository")
    names: set[str] = set()
    for entry in manifest.get("destinations") or []:
        repository = entry.get("repository")
        if repository:
            names.add(repository)
    for entry in manifest.get("paths") or []:
        repository = entry.get("repository")
        if repository and repository != donor:
            names.add(repository)
    return names


def _destination_receipts_cover(manifest: dict[str, Any]) -> bool:
    repositories = _destination_repositories(manifest)
    if not repositories:
        return False
    present = {repository: set() for repository in repositories}
    for receipt_entry in manifest.get("receipts") or []:
        if receipt_entry.get("kind") not in {"row", "whole-session"}:
            continue
        if not _receipt_ok(receipt_entry, manifest):
            return False
        repository = receipt_entry.get("repository")
        if repository in present:
            present[repository].add(receipt_entry["kind"])
    needed = {"row", "whole-session"}
    return all(needed <= kinds for kinds in present.values())


def _expand_grant(grant: str, files: list[str]) -> list[str]:
    if grant.endswith("/"):
        return [path for path in files if path.startswith(grant)]
    if "*" in grant or "?" in grant:
        from fnmatch import fnmatch
        return [path for path in files if fnmatch(path, grant)]
    if grant in files:
        return [grant]
    prefix = grant.rstrip("/") + "/"
    nested = [path for path in files if path.startswith(prefix)]
    return nested


def _covers_requested_donor(manifest: dict[str, Any], spec: dict[str, Any]) -> bool:
    """A covering manifest names the gateway donor at the requested revision."""
    donor = manifest.get("donor") or {}
    requested_repository = spec.get("donor_repository") or "gateway"
    return donor.get("repository") == requested_repository and donor.get("sha") == spec.get("donor_sha")


def _manifest_covers_classifier(manifest: dict[str, Any]) -> bool:
    """True when the donor side of this manifest includes the offline classifier."""
    donor = (manifest.get("donor") or {}).get("repository")
    for entry in manifest.get("paths") or []:
        if entry.get("repository") != donor:
            continue
        for path in entry.get("paths") or []:
            if str(path).startswith(CLASSIFIER_PREFIXES):
                return True
    for symbol in manifest.get("symbols") or []:
        if str(symbol.get("file") or "").startswith(CLASSIFIER_PREFIXES):
            return True
    return False


def _classifier_destination_revisions(manifest: dict[str, Any]) -> set[tuple[str, str]]:
    """Repository and commit pairs already recorded for the classifier destination.

    The pair is the destination repository of a classifier symbol, or of a
    sealed destination path under the classifier prefixes, together with the
    destination commit of a passing row or whole-session receipt for that
    repository. A standalone receipt has to name one of those pairs.
    """
    names = {
        symbol["name"]
        for symbol in manifest.get("symbols") or []
        if str(symbol.get("file") or "").startswith(CLASSIFIER_PREFIXES)
    }
    repositories: set[str] = set()
    for entry in manifest.get("destinations") or []:
        if entry.get("kind") == "symbol" and entry.get("name") in names and entry.get("repository"):
            repositories.add(entry["repository"])
    donor = (manifest.get("donor") or {}).get("repository")
    for entry in manifest.get("paths") or []:
        repository = entry.get("repository")
        if not repository or repository == donor:
            continue
        for path in entry.get("paths") or []:
            if str(path).startswith(CLASSIFIER_PREFIXES):
                repositories.add(repository)
    revisions: set[tuple[str, str]] = set()
    for receipt_entry in manifest.get("receipts") or []:
        if receipt_entry.get("kind") not in {"row", "whole-session"}:
            continue
        if not _receipt_ok(receipt_entry, manifest):
            continue
        repository = receipt_entry.get("repository")
        commit = receipt_entry.get("destination_commit")
        if repository in repositories and commit:
            revisions.add((str(repository), str(commit)))
    return revisions


def _standalone_binds_classifier(receipt_entry: dict[str, Any], manifest: dict[str, Any]) -> bool:
    """True when this receipt is the classifier destination's own standalone proof."""
    if receipt_entry.get("kind") != "standalone-classifier" or not _receipt_ok(receipt_entry, manifest):
        return False
    compared = set(receipt_entry.get("compared") or [])
    if any(surface not in compared for surface in CLASSIFIER_SURFACES):
        return False
    if not _manifest_covers_classifier(manifest):
        return False
    named = (str(receipt_entry.get("repository") or ""), str(receipt_entry.get("destination_commit") or ""))
    return named in _classifier_destination_revisions(manifest)


def deletion(spec: dict[str, Any], gateway: Path) -> int:
    row = spec["row"]
    if row not in DELETION_ROWS:
        return emit([f"row: {row}"])
    ledger_commit = spec["ledger_commit"]
    if not gitstore.commit_exists(gateway, ledger_commit):
        return emit([f"ledger-absent: tools/boundary"])
    ledger_listing = gitstore.run_git(
        gateway, ["ls-tree", "-r", "--name-only", ledger_commit, "tools/boundary"], check=False
    )
    if ledger_listing.returncode != 0 or not ledger_listing.stdout.strip():
        return emit(["ledger-absent: tools/boundary"])
    ledger_paths = [line for line in ledger_listing.stdout.splitlines() if line]
    blobs = gitstore.read_blobs(gateway, ledger_commit, ledger_paths)
    findings = []
    for path, blob in blobs.items():
        for line in blob.decode(errors="replace").splitlines():
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) != 4:
                continue
            finding_path, kind, item, owner = parts
            if owner == row:
                findings.append({"path": finding_path, "kind": kind, "item": item})
    manifest_paths = [Path(item) for item in spec["manifests"]]
    manifests = [load_json(path) for path in manifest_paths]
    errors: list[str] = []
    for finding in findings:
        covered = False
        for manifest in manifests:
            donor_paths: list[str] = []
            for entry in manifest["paths"]:
                if entry["repository"] == manifest["donor"]["repository"]:
                    donor_paths.extend(entry["paths"])
            symbol_files = {item["file"] for item in manifest["symbols"]}
            if finding["path"] not in donor_paths and finding["path"] not in symbol_files:
                continue
            if not _covers_requested_donor(manifest, spec):
                continue
            if _destination_receipts_cover(manifest):
                covered = True
        if not covered:
            errors.append(f"missing-receipt: {finding['path']}")
    covering = [manifest for manifest in manifests if _manifest_covers_classifier(manifest)]
    if covering and not any(
        _standalone_binds_classifier(receipt_entry, manifest)
        for manifest in covering
        for receipt_entry in manifest.get("receipts") or []
    ):
        errors.append("missing-receipt: standalone-classifier")
    files = gitstore.list_files_recursive(gateway, ledger_commit)
    lines: list[str] = [finding["path"] for finding in findings]
    reserves = list(spec.get("reserves") or [])
    for grant in spec.get("grants") or []:
        path = grant["path"]
        if path == f"@paths/{row}.lst":
            continue
        expanded = _expand_grant(path, files)
        if expanded:
            lines.extend(expanded)
            continue
        under = [item for item in reserves if item.startswith(path.rstrip("/") + "/")]
        if under:
            lines.extend(under)
            continue
        errors.append(f"grant-empty: {path}")
    if row == "GG11":
        prefix = GG11_DIR + "/"
        granted = any(
            item["path"].rstrip("/") == GG11_DIR or item["path"].startswith(prefix)
            for item in spec.get("grants") or []
        )
        if granted:
            fixture_lines = [item for item in lines if item.startswith(prefix)]
            if len(fixture_lines) != 5 or len({item for item in reserves if item.startswith(prefix)}) != 5:
                errors.append("gg11-fixtures")
    if row == "GG10":
        evidence = spec.get("retirement_evidence")
        if not isinstance(evidence, dict):
            errors.append("missing-retirement-evidence")
        else:
            if not evidence.get("r2_002") or not evidence.get("r2_057"):
                errors.append("missing-retirement-evidence")
            for key in (
                "qq08_offline_validator",
                "pinned_offline_capture_comparison",
                "caller_inventory",
            ):
                block = evidence.get(key) or {}
                if not block.get("revision") or not block.get("result"):
                    errors.append("missing-retirement-evidence")
            covered_ids = set()
            for item in evidence.get("live_inputs") or []:
                if item.get("disposition") and item.get("closure") and item.get("source_revision"):
                    covered_ids.add(item.get("id"))
                else:
                    errors.append(f"uncovered-live-input: {item.get('id', '')}")
            for live in spec.get("live_inputs") or []:
                if live not in covered_ids:
                    errors.append(f"uncovered-live-input: {live}")
            if "internal/eebusoutput/binding.go" in lines:
                relay = evidence.get("relay") or {}
                if relay.get("production_callers") != "absent" or not relay.get("testm40_outcome") or not relay.get("revision"):
                    errors.append("missing-retirement-evidence: internal/eebusoutput/binding.go")
            for shared in SHARED_PRODUCTION:
                if shared in lines:
                    mark = None
                    for item in evidence.get("shared_paths") or []:
                        if item.get("path") == shared:
                            mark = item
                    if not mark or not mark.get("ordinary_receipts") or not mark.get("offline_retirement"):
                        errors.append(f"missing-retirement-evidence: {shared}")
    if errors:
        return emit(errors)
    ordered = sorted(set(lines))
    payload = list_bytes(ordered)
    directory = manifest_dir()
    directory.mkdir(parents=True, exist_ok=True)
    list_path = directory / f"{row}.lst"
    list_path.write_bytes(payload)
    recorded = {
        "row": row,
        "repository": "gateway",
        "donor_sha": spec["donor_sha"],
        "sha256": digest(payload),
    }
    (directory / f"{row}.json").write_text(dump(recorded), encoding="utf-8")
    import sys
    sys.stdout.write(payload.decode())
    return 0
