#!/usr/bin/env python3
"""Environment check for the position/order study.

Run from the repository root:
    python scripts/env_check.py
    python scripts/env_check.py --server-url http://127.0.0.1:8080   # optional

What it does: reads the system and Python environment, runs a few small checks,
prints one line per check (PASS / WARN / FAIL / INFO), and writes a JSON report
to results/env/env_report.json. It does not download anything, does not run a
model, and does not change any file except the report.

Exit code: 0 if no check FAILED, 1 otherwise. WARN does not change the exit code.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib
import importlib.metadata as md
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

RESULTS: list[dict] = []


def record(status: str, name: str, detail: str = "") -> None:
    RESULTS.append({"status": status, "check": name, "detail": detail})
    print(f"[{status}] {name}" + (f": {detail}" if detail else ""))


def run(cmd: list[str], timeout: int = 60) -> tuple[int, str]:
    """Run a command; return (return code, combined output). Never raises."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except FileNotFoundError:
        return 127, "executable not found"
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout}s"
    except Exception as exc:  # defensive: report, do not crash
        return 1, f"{type(exc).__name__}: {exc}"


def load_config(path: Path) -> dict:
    try:
        import yaml  # noqa: WPS433

        with open(path, "r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except Exception as exc:
        record("FAIL", "config", f"cannot read {path}: {type(exc).__name__}: {exc}")
        return {}


def check_python() -> None:
    in_venv = sys.prefix != getattr(sys, "base_prefix", sys.prefix)
    record("INFO", "python", f"{platform.python_version()} at {sys.executable}")
    record("PASS" if in_venv else "WARN", "virtual environment",
           "active" if in_venv else "not active; use a project virtual environment")
    record("INFO", "system", f"{platform.system()} {platform.release()} ({platform.machine()})")


def check_packages() -> None:
    required = {"numpy": "numpy", "pandas": "pandas", "scipy": "scipy", "pyyaml": "yaml",
                "requests": "requests", "psutil": "psutil"}
    optional = {"tqdm": "tqdm", "huggingface_hub": "huggingface_hub", "pytest": "pytest"}
    for dist, mod in {**required, **optional}.items():
        is_required = dist in required
        try:
            importlib.import_module(mod)
            record("PASS", f"package {dist}", md.version(dist))
        except Exception as exc:
            record("FAIL" if is_required else "WARN", f"package {dist}",
                   f"import failed: {type(exc).__name__}: {exc}")
    rc, out = run([sys.executable, "-m", "pip", "check"])
    first = out.splitlines()[0] if out else ""
    if rc == 0:
        record("PASS", "pip check", first or "no broken requirements reported")
    else:
        record("FAIL", "pip check", "; ".join(out.splitlines()[:5]) or f"return code {rc}")


def check_gpu() -> None:
    exe = shutil.which("nvidia-smi")
    if not exe:
        record("FAIL", "nvidia-smi", "not found on PATH (NVIDIA driver missing or PATH issue)")
        return
    rc, out = run([exe, "--query-gpu=name,memory.total,memory.used,driver_version",
                   "--format=csv,noheader"])
    if rc != 0 or not out:
        record("FAIL", "GPU query", f"return code {rc}: {out[:200]}")
        return
    for i, line in enumerate(out.splitlines()):
        record("INFO", f"GPU {i}", line.strip())
    rc2, head = run([exe])
    m = re.search(r"CUDA Version:\s*([0-9.]+)", head or "")
    record("INFO", "driver-supported CUDA version",
           m.group(1) if m else "not parsed from nvidia-smi header")
    record("PASS", "GPU visible", f"{len(out.splitlines())} device(s)")


def check_memory_disk() -> None:
    try:
        import psutil

        vm = psutil.virtual_memory()
        record("INFO", "RAM", f"total {vm.total / 2**30:.1f} GiB, available {vm.available / 2**30:.1f} GiB")
        free = shutil.disk_usage(ROOT).free / 2**30
        # 10 GiB is a threshold chosen for this project, not a measured requirement.
        record("PASS" if free >= 10 else "WARN", "free disk space",
               f"{free:.1f} GiB free at {ROOT} (threshold 10 GiB, adjustable)")
    except Exception as exc:
        record("WARN", "RAM/disk", f"{type(exc).__name__}: {exc}")


def check_llama_server(cfg: dict) -> None:
    exe_cfg = (cfg.get("server") or {}).get("executable", "llama-server")
    exe = shutil.which(exe_cfg) or (exe_cfg if Path(exe_cfg).exists() else None)
    if not exe:
        record("FAIL", "llama-server", f"'{exe_cfg}' not found (install it; see README)")
        return
    record("INFO", "llama-server path", str(exe))
    rc, out = run([exe, "--version"])
    record("PASS" if rc == 0 else "FAIL", "llama-server --version",
           (out.splitlines()[0] if out else f"return code {rc}")[:200])
    rc, helptext = run([exe, "--help"])
    for flag in ("--ctx-size", "--n-gpu-layers", "--seed"):
        record("PASS" if flag in helptext else "WARN", f"llama-server flag {flag}",
               "listed in --help" if flag in helptext else "not found in --help (name may differ in your build)")
    # Whether this build has GPU support is not detectable here; check the server log
    # at start-up for a line about layers offloaded to the GPU.
    record("INFO", "GPU offload", "confirm in the server start-up log; not detectable by this script")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def check_files(cfg: dict) -> None:
    paths = cfg.get("paths") or {}
    model = ROOT / paths.get("model_file", "models/MISSING.gguf")
    if model.is_file():
        record("PASS", "model file", f"{model.name}, {model.stat().st_size / 2**30:.2f} GiB")
        record("INFO", "model sha256 (record this)", sha256_of(model))
    else:
        record("WARN", "model file", f"not found at {model} (expected before the first run)")
    data = ROOT / paths.get("retrieval_file", "data/raw/MISSING")
    if data.is_file():
        record("PASS", "retrieval data file", f"{data.name}, {data.stat().st_size / 2**20:.1f} MiB")
        record("INFO", "retrieval file sha256 (record this)", sha256_of(data))
    else:
        record("WARN", "retrieval data file", f"not found at {data} (expected before data preparation)")


def check_seeds(cfg: dict) -> None:
    try:
        from positionorder.seeds import derive_seed, distractor_permutation, set_global_seed

        s = (cfg.get("seeds") or {})
        o1, o2 = s.get("ordering_o1", 101), s.get("ordering_o2", 202)
        a = distractor_permutation(o1, "q-test")
        b = distractor_permutation(o1, "q-test")
        c = distractor_permutation(o2, "q-test")
        ok_repeat = a == b and sorted(a) == list(range(19))
        ok_differ = a != c
        # Independence from call order
        ids = ["a", "b", "c"]
        fwd = {q: distractor_permutation(o1, q) for q in ids}
        bwd = {q: distractor_permutation(o1, q) for q in reversed(ids)}
        ok_order = fwd == bwd
        # Stability across processes (guards against hash() salting)
        code = ("import sys;sys.path.insert(0,r'%s');"
                "from positionorder.seeds import derive_seed;print(derive_seed(%d,'q-test'))"
                % (str(ROOT / "src"), o1))
        rc, out = run([sys.executable, "-c", code])
        ok_proc = rc == 0 and out.strip() == str(derive_seed(o1, "q-test"))
        set_global_seed(s.get("split", 1234))
        record("PASS" if ok_repeat else "FAIL", "seed: permutation repeatable", "")
        record("PASS" if ok_differ else "FAIL", "seed: O1 and O2 differ", "")
        record("PASS" if ok_order else "FAIL", "seed: independent of call order", "")
        record("PASS" if ok_proc else "FAIL", "seed: stable across processes", out[:80] if not ok_proc else "")
    except Exception as exc:
        record("FAIL", "seed controls", f"{type(exc).__name__}: {exc}")


def check_server_url(url: str) -> None:
    try:
        import requests

        for ep in ("/health", "/v1/models"):
            try:
                r = requests.get(url.rstrip("/") + ep, timeout=5)
                record("PASS" if r.ok else "WARN", f"server {ep}", f"HTTP {r.status_code}")
                if r.ok:
                    return
            except Exception as exc:
                record("WARN", f"server {ep}", f"{type(exc).__name__}")
        record("WARN", "server reachable", "neither endpoint answered; is llama-server running?")
    except Exception as exc:
        record("WARN", "server check", f"{type(exc).__name__}: {exc}")


def git_state() -> dict:
    rc, head = run(["git", "-C", str(ROOT), "rev-parse", "HEAD"])
    rc2, dirty = run(["git", "-C", str(ROOT), "status", "--porcelain"])
    return {"commit": head if rc == 0 else None,
            "dirty": bool(dirty) if rc2 == 0 else None}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", default=str(ROOT / "configs" / "protocol_v0.1.yaml"))
    ap.add_argument("--report", default=str(ROOT / "results" / "env" / "env_report.json"))
    ap.add_argument("--server-url", default=None, help="optional, e.g. http://127.0.0.1:8080")
    args = ap.parse_args()

    print(f"Environment check, {dt.datetime.now().astimezone().isoformat(timespec='seconds')}")
    print("-" * 72)
    check_python()
    cfg = load_config(Path(args.config))
    check_packages()
    check_gpu()
    check_memory_disk()
    check_llama_server(cfg)
    check_files(cfg)
    check_seeds(cfg)
    if args.server_url:
        check_server_url(args.server_url)

    counts = {k: sum(1 for r in RESULTS if r["status"] == k) for k in ("PASS", "WARN", "FAIL", "INFO")}
    print("-" * 72)
    print(f"SUMMARY: {counts['PASS']} PASS, {counts['WARN']} WARN, {counts['FAIL']} FAIL, {counts['INFO']} INFO")

    report = {"created": dt.datetime.now().astimezone().isoformat(timespec="seconds"),
              "protocol_version": cfg.get("protocol_version"),
              "python": platform.python_version(), "platform": platform.platform(),
              "git": git_state(), "counts": counts, "checks": RESULTS}
    out = Path(args.report)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Report written to {out}")
    return 1 if counts["FAIL"] else 0


if __name__ == "__main__":
    sys.exit(main())
