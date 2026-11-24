"""Shared helpers of the oracle recorders. Reads the pins from references.json; holds no pin of its own."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ORACLE = Path(__file__).resolve().parent.parent
ROOT = ORACLE.parent.parent
REFERENCES = ORACLE / "references.json"


def references():
    return json.loads(REFERENCES.read_text(encoding="utf-8"))["references"]


def entry(reference, entry_id):
    for item in references()[reference]["entries"]:
        if item["id"] == entry_id:
            return item
    raise KeyError(f"{reference}/{entry_id}")


def donor_root():
    value = os.environ.get("ORACLE_DONOR_ROOT")
    if not value:
        sys.exit("ORACLE_DONOR_ROOT is not set: it names the directory that holds one clone per slug_at_pin")
    return Path(value)


def donor_repo(item):
    return donor_root() / item["slug_at_pin"]


def scratch_root():
    value = os.environ.get("ORACLE_SCRATCH")
    path = Path(value) if value else ROOT / ".tmp" / "oracle-scratch"
    path.mkdir(parents=True, exist_ok=True)
    return path


def unpack(item, destination=None):
    """git archive of the pinned commit into a scratch directory; the clone is never touched."""
    destination = Path(destination) if destination else scratch_root() / "src" / f"{item['slug_at_pin']}-{item['commit'][:12]}"
    if destination.exists():
        return destination
    destination.mkdir(parents=True)
    archive = subprocess.run(["git", "-C", str(donor_repo(item)), "archive", item["commit"]], check=True, stdout=subprocess.PIPE).stdout
    subprocess.run(["tar", "-x", "-C", str(destination)], input=archive, check=True)
    return destination


def show(item, path):
    result = subprocess.run(["git", "-C", str(donor_repo(item)), "show", f"{item['commit']}:{path}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode != 0:
        return None
    return result.stdout


def proxy_dir():
    path = scratch_root() / "module-proxy"
    path.mkdir(parents=True, exist_ok=True)
    return path


def go_env(extra=None):
    env = dict(os.environ)
    env.update({"GOWORK": "off", "GOPROXY": "file://" + str(proxy_dir()), "GOSUMDB": "off", "GOFLAGS": "-mod=mod", "GOTOOLCHAIN": "auto", "CGO_ENABLED": env.get("CGO_ENABLED", "0")})
    cache = scratch_root() / "gocache"
    env.setdefault("GOCACHE", str(cache))
    if extra:
        env.update(extra)
    return env


def canonical(value):
    return json.dumps(value, indent=2, sort_keys=False, ensure_ascii=False) + "\n"


def write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        data = data.encode("utf-8")
    path.write_bytes(data)


def clean(path):
    if Path(path).exists():
        shutil.rmtree(path)


ALIASES = {"helianthus-matterreg": "helianthus-matter-binding", "helianthus-gateway": "helianthus-ebusgateway"}


def _escape(text):
    import re
    return re.sub(r"[A-Z]", lambda m: "!" + m.group(0).lower(), text)


def _h1(files):
    import base64
    import hashlib
    lines = "".join(f"{hashlib.sha256(data).hexdigest()}  {name}\n" for name, data in sorted(files.items()))
    return "h1:" + base64.b64encode(hashlib.sha256(lines.encode()).digest()).decode()


def _serve(module, version, mod_bytes, when, files):
    import zipfile
    target = proxy_dir() / _escape(module) / "@v"
    target.mkdir(parents=True, exist_ok=True)
    stem = _escape(version)
    (target / (stem + ".mod")).write_bytes(mod_bytes)
    (target / (stem + ".info")).write_text(json.dumps({"Version": version, "Time": when}))
    listing = target / "list"
    known = set(listing.read_text().split()) if listing.exists() else set()
    known.add(version)
    listing.write_text("".join(v + "\n" for v in sorted(known)))
    if files is not None:
        prefix = f"{module}@{version}/"
        with zipfile.ZipFile(target / (stem + ".zip"), "w", zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(files.items()):
                archive.writestr(prefix + name, data)


def materialize(module, version):
    """Serve one module version the module cache lacks, from the extracted module cache or from a donor clone.

    go.sum verifies the .mod and zip bytes, so a wrong reconstruction fails loudly rather than passing."""
    import datetime
    import re
    cache = Path(os.environ.get("GOMODCACHE") or subprocess.run(["go", "env", "GOMODCACHE"], stdout=subprocess.PIPE, text=True).stdout.strip())
    extracted = cache / (_escape(module) + "@" + _escape(version))
    if extracted.is_dir():
        files = {}
        for path in sorted(extracted.rglob("*")):
            if path.is_file():
                files[path.relative_to(extracted).as_posix()] = path.read_bytes()
        mod_bytes = files.get("go.mod", f"module {module}\n".encode())
        _serve(module, version, mod_bytes, "2000-01-01T00:00:00Z", files)
        return True
    name = module.rsplit("/", 1)[-1]
    name = ALIASES.get(name, name)
    repo = donor_root() / name
    if not module.startswith("github.com/Project-Helianthus/") or not repo.exists():
        return False
    pseudo = re.search(r"[-.](\d{14})-([0-9a-f]{12})$", version)
    ref = pseudo.group(2) if pseudo else version
    found = subprocess.run(["git", "-C", str(repo), "rev-parse", "--verify", ref + "^{commit}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if found.returncode != 0:
        return False
    commit = found.stdout.strip()
    listing = subprocess.run(["git", "-C", str(repo), "ls-tree", "-r", "-z", "--name-only", commit], stdout=subprocess.PIPE, check=True).stdout.decode().split("\0")
    files = {}
    for name_ in listing:
        if not name_ or name_.split("/")[0] == "vendor":
            continue
        files[name_] = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:{name_}"], stdout=subprocess.PIPE, check=True).stdout
    nested = {n.rsplit("/", 1)[0] for n in files if n.endswith("/go.mod")}
    files = {n: d for n, d in files.items() if not any(n.startswith(x + "/") for x in nested)}
    mod_bytes = files.get("go.mod", f"module {module}\n".encode())
    if pseudo:
        when = datetime.datetime.strptime(pseudo.group(1), "%Y%m%d%H%M%S").strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        when = subprocess.run(["git", "-C", str(repo), "log", "-1", "--format=%cI", commit], stdout=subprocess.PIPE, text=True).stdout.strip()
    _serve(module, version, mod_bytes, when, files)
    return True


def go_run(args, cwd, env=None, attempts=400):
    """Run go, serving each module version it reports as unavailable offline, then retrying."""
    import re
    env = env or go_env()
    seen = set()
    for _ in range(attempts):
        result = subprocess.run(["go"] + args, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            return result
        found = set(re.findall(r"(?m)(?:^go: |downloading )(\S+?)[@ ](v\S+?)(?::|$| )", result.stderr))
        fresh = {x for x in found if x not in seen}
        done = False
        for module, version in sorted(fresh):
            seen.add((module, version))
            done = common_materialize(module, version) or done
        if not done:
            return result
    return result


def common_materialize(module, version):
    return materialize(module, version)
