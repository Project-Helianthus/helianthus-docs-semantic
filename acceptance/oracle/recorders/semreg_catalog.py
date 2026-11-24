#!/usr/bin/env python3
"""Extract the element catalog bytes that semreg embeds in v1/graph/enforcement.go, with their sha256 (SS03 vector)."""

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402


def record(output):
    item = common.entry("current", "semreg")
    source = common.unpack(item)
    text = (source / "semreg/v1/graph/enforcement.go").read_text(encoding="utf-8")
    start = text.index("const embeddedCatalog = `") + len("const embeddedCatalog = `")
    end = text.index("`", start)
    embedded = text[start:end].encode("utf-8")
    fixture = (source / "fixtures/v1/element-catalog-v1.json").read_bytes()
    digest_line = re.search(r'const PinnedDigest semreg\.Digest = "([^"]+)"', (source / "semreg/v1/graph/catalog.go").read_text(encoding="utf-8"))
    document = {
        "format": "helianthus-oracle-semreg-embedded-catalog/1",
        "source": {"repository": item["slug_at_pin"], "commit": item["commit"], "path": "semreg/v1/graph/enforcement.go", "constant": "embeddedCatalog"},
        "embedded_bytes": len(embedded),
        "embedded_sha256": hashlib.sha256(embedded).hexdigest(),
        "pinned_digest_constant": digest_line.group(1) if digest_line else None,
        "fixture": {"path": "fixtures/v1/element-catalog-v1.json", "sha256": hashlib.sha256(fixture).hexdigest(), "equal_to_embedded_bytes": fixture == embedded},
    }
    common.write(output, common.canonical(document))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    record(parser.parse_args().output)


if __name__ == "__main__":
    main()
