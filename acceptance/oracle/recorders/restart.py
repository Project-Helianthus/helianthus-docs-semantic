#!/usr/bin/env python3
"""The two lifecycles of the restart vectors (item 7) and the defect mark of item 15.

Each cut file holds a `compared` object: sorted node IDs, the nodes with their kind, home and anchor, the link keys with endpoints and
types, the aliases the allocator store holds, the links of each source and the consumer value keys. Only those members are compared.
Clocks, leases, cut digests, the export result, the values of each source and their presentation are outside the comparison."""

import json
from pathlib import Path

CUTS = ("cut-first.json", "cut-second.json")
DIRECTORY = "current/restart"
COMPARED = ("node_ids", "nodes", "link_keys", "aliases", "source_links", "consumer_value_keys")
DEFECT_ITEM = 15
DEFECT_OWNER = "SS05 and SS06"
MISSING = object()


def load(directory):
    return [json.loads((Path(directory) / name).read_text(encoding="utf-8")) for name in CUTS]


def differences(first, second):
    """(member, first value, second value) for each compared member that differs; a member absent from either cut differs."""
    left, right = first.get("compared"), second.get("compared")
    if not isinstance(left, dict) or not isinstance(right, dict):
        return [("compared", left, right)]
    found = []
    for member in COMPARED:
        a, b = left.get(member, MISSING), right.get(member, MISSING)
        if a is MISSING or b is MISSING or a != b:
            found.append((member, "absent" if a is MISSING else a, "absent" if b is MISSING else b))
    return found


def mark(entries, first, second):
    """Add the item 15 defect mark to the index entries of both cuts when the lifecycles differ; return the entries."""
    members = [member for member, _left, _right in differences(first, second)]
    if not members:
        return entries
    for entry in entries:
        if entry["path"].startswith(DIRECTORY + "/"):
            entry["defect"] = {"item": DEFECT_ITEM, "owner": DEFECT_OWNER, "members": members}
    return entries


def marked_members(entries):
    """The compared members the index marks as an item 15 defect on either cut."""
    found = set()
    for entry in entries:
        defect = entry.get("defect")
        if entry["path"].startswith(DIRECTORY + "/") and isinstance(defect, dict) and defect.get("item") == DEFECT_ITEM:
            found.update(defect.get("members", []))
    return found
