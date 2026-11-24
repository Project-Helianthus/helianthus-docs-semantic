import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare  # noqa: E402

FABRIC = compare.FABRIC
DEP = "github.com/example/dep"


def mod(path, version, sum_, go_mod_sum="h1:gomod"):
    return {"path": path, "version": version, "sum": sum_, "go_mod_sum": go_mod_sum}


def repo(go="1.27.4", fabric_version="v0.22.2", extra=()):
    modules = [
        mod(DEP, "v1.0.0", "h1:dep"),
        mod(FABRIC, fabric_version, "h1:fabric"),
    ]
    modules.extend(extra)
    return {
        "main": {"path": "github.com/Project-Helianthus/helianthus-matter-binding", "go": go},
        "modules": modules,
    }


def renamed_repo(**kwargs):
    r = repo(**kwargs)
    r["main"]["path"] = "github.com/Project-Helianthus/helianthus-matterreg"
    return r


def classes(pairs):
    return [p["class"] for p in pairs]


class CompareTests(unittest.TestCase):
    def test_unchanged_repository_has_no_unexplained_pairs(self):
        pairs, _ = compare.compare_repository("matterreg", repo(), renamed_repo())
        self.assertNotIn("unexplained", classes(pairs))

    def test_repin_does_not_exempt_unrelated_dependency_checksum_change(self):
        after = renamed_repo(fabric_version="v0.23.0")
        after["modules"][0] = mod(DEP, "v1.0.0", "h1:tampered")
        pairs, _ = compare.compare_repository("matterreg", repo(), after)
        dep = [p for p in pairs if p["kind"] == "module" and p["before_path"] == DEP]
        self.assertEqual(["unexplained"], classes(dep))

    def test_repin_does_not_exempt_added_unrelated_module(self):
        after = renamed_repo(fabric_version="v0.23.0")
        after["modules"].append(mod("github.com/example/new", "v2.0.0", "h1:new"))
        pairs, _ = compare.compare_repository("matterreg", repo(), after)
        added = [p for p in pairs if p["kind"] == "module" and p["before_path"] is None]
        self.assertEqual(["unexplained"], classes(added))

    def test_repin_does_not_exempt_go_directive_change(self):
        after = renamed_repo(go="1.28.0", fabric_version="v0.23.0")
        pairs, _ = compare.compare_repository("matterreg", repo(), after)
        go = [p for p in pairs if p["kind"] == "go"]
        self.assertEqual(["unexplained"], classes(go))

    def test_repin_exempts_only_the_go_fabric_requirement(self):
        after = renamed_repo(fabric_version="v0.23.0")
        pairs, fabric = compare.compare_repository("matterreg", repo(), after)
        self.assertEqual({"before": "v0.22.2", "after": "v0.23.0"}, fabric)
        fab = [p for p in pairs if p["kind"] == "module" and p["before_path"] == FABRIC]
        self.assertEqual(["go-fabric re-pin"], classes(fab))
        self.assertNotIn("unexplained", classes(pairs))

    def test_replacement_added_to_dependency_is_unexplained(self):
        after = renamed_repo()
        after["modules"][0] = copy.deepcopy(after["modules"][0])
        after["modules"][0]["replace"] = {
            "path": "github.com/fork/dep",
            "version": "v1.0.0",
            "sum": "h1:fork",
        }
        pairs, _ = compare.compare_repository("matterreg", repo(), after)
        dep = [p for p in pairs if p["kind"] == "module" and p["before_path"] == DEP]
        self.assertEqual(["unexplained"], classes(dep))

    def test_replacement_change_is_unexplained_even_with_original_version(self):
        before = repo()
        before["modules"][0] = mod(DEP, "v1.0.0", "h1:dep")
        before["modules"][0]["replace"] = {"path": "github.com/fork/dep", "version": "v1.0.0", "sum": "h1:a"}
        after = renamed_repo()
        after["modules"][0] = mod(DEP, "v1.0.0", "h1:dep")
        after["modules"][0]["replace"] = {"path": "github.com/fork/dep", "version": "v1.0.0", "sum": "h1:b"}
        pairs, _ = compare.compare_repository("matterreg", before, after)
        dep = [p for p in pairs if p["kind"] == "module" and p["before_path"] == DEP]
        self.assertEqual(["unexplained"], classes(dep))


if __name__ == "__main__":
    unittest.main()
