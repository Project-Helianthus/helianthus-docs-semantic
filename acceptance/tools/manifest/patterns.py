"""Pattern signatures: selector geometry plus the inverse pattern.

A signature matches an exemplar row only when the two objects are equal.
Concrete operands are not part of the signature. They are checked against
the row's own vectors and against the inverse the signature names.
"""

from __future__ import annotations

import json
from typing import Any


def canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def same_signature(left: Any, right: Any) -> bool:
    return canonical(left) == canonical(right)


def parse_rows(blob: bytes) -> list[dict[str, Any]]:
    text = blob.decode(errors="replace")
    stripped = text.lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        data = json.loads(text)
        if isinstance(data, dict) and isinstance(data.get("rows"), dict):
            rows = []
            for key, value in data["rows"].items():
                row = dict(value)
                row.setdefault("id", key)
                rows.append(row)
            return rows
        if isinstance(data, dict) and "signature" in data:
            return [data]
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        raise ValueError("pattern file has no rows")
    rows = []
    for line in text.splitlines():
        marker = "QQ06ROW"
        if marker not in line:
            continue
        payload = line.split(marker, 1)[1].strip()
        rows.append(json.loads(payload))
    return rows


def operand_problem(signature: dict[str, Any], operands: dict[str, Any]) -> str | None:
    """Return a short reason when concrete operands break the inverse."""
    inverse = signature.get("inverse")
    described = canonical(inverse) if inverse is not None else ""
    if "same-keyed-disable" in described:
        selected = operands.get("limit_id")
        inverse_limit = operands.get("inverse_limit_id", operands.get("disable_key"))
        if selected is None or inverse_limit != selected:
            return "inverse-limit"
    if "same-instance" in described:
        if operands.get("readback_instance") != operands.get("instance"):
            return "readback-instance"
    if "same-slot" in described:
        if operands.get("readback_slot") != operands.get("slot"):
            return "readback-slot"
        if operands.get("readback_series") != operands.get("series"):
            return "readback-series"
    if "same-tariff" in described:
        if operands.get("readback_tariff") != operands.get("tariff"):
            return "readback-tariff"
    return None


def selector_problem(
    signature: dict[str, Any],
    operands: dict[str, Any],
    selectors: dict[str, Any],
) -> str | None:
    """Concrete selector values must be the values in this row's vector."""
    fields = signature.get("selector_fields") or []
    for field in fields:
        if field not in operands:
            continue
        if field not in selectors or selectors[field] != operands[field]:
            return field
    return None
