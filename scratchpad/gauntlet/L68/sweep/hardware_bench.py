"""Benchmark this machine and report it with the hardware that produced it.

    python hardware_bench.py --root ~/Royale
    python hardware_bench.py --root ~/Royale --profile workstation --iterations 5

WHY NOT JUST `royalelearn bench`. That command measures the throughput table and it is the right
measurement -- this wraps it rather than replacing it. What it does not record is the machine, and
a throughput number without the hardware that produced it cannot be compared with anything.

THE SPECIFIC THING THAT MAKES THAT NOT PEDANTRY, measured on the reference laptop on 2026-09-23:
after about seven hours at 96% utilisation, the same fixed-size critic pass went from 25.3 s to
48.5 s -- a 92% slowdown with no change to the batch, the model or the data. The cause was the GPU
sitting at 1620 MHz of a 2100 MHz maximum with `sw_power_cap` ACTIVE. Nothing in the throughput
table says that, so two runs of `bench` on the same machine can differ by nearly 2x and look like
a software regression.

So this SAMPLES THE GPU WHILE THE BENCHMARK RUNS rather than before it. A clock read at rest is
not the clock the benchmark got.

WHAT IT REFUSES TO DO. It will not silently pick a profile whose assumptions the machine does not
meet. `workstation` assumes 32 GB RAM and 12 GB VRAM; a card with 8 GB satisfies one axis and not
the other, and choosing on RAM alone is how a benchmark turns into an out-of-memory error twenty
minutes in. When the axes disagree it says so and picks the safe one.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import subprocess
import sys
import threading
import time
from pathlib import Path

#: The reference machine, so a first run is comparable without having to find these numbers.
#: Measured 2026-09-23 on the laptop this project is developed on, laptop profile, float32.
REFERENCE = {
    "label": "RTX 3050 Laptop / 7.9 GB RAM (the development machine)",
    "gpu": "NVIDIA GeForce RTX 3050 Laptop GPU",
    "vram_total_mb": 4096,
    "ram_total_mb": 7938,
    "profile": "laptop",
    "dtype": "float32",
    "seconds_per_iteration_cold": 62.0,
    "seconds_per_iteration_power_capped": 90.9,
    "critic_pass_seconds_cold": 25.3,
    "critic_pass_seconds_power_capped": 48.5,
    "collected_steps_per_second": 2905,
    "vram_peak_mb": 1882,
    "note": (
        "The two columns are the SAME run seven hours apart. The slowdown is the GPU falling to "
        "1620 MHz of 2100 with sw_power_cap active, not a software change. bfloat16 on this "
        "machine is 26.9 s/iteration but cannot carry a large no-op bias: its rounding breaks "
        "PPO's importance-ratio invariant."
    ),
}

PROFILE_NEEDS = {
    "laptop": {"ram_gb": 8, "vram_gb": 4},
    "workstation": {"ram_gb": 32, "vram_gb": 12},
    "many_core": {"ram_gb": 64, "vram_gb": 24},
}


def sh(cmd, cwd=None, timeout=None):
    try:
        p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr).strip()
    except (OSError, subprocess.TimeoutExpired) as exc:
        return 1, str(exc)


def nvidia(fields: str) -> list[str]:
    code, out = sh(["nvidia-smi", f"--query-gpu={fields}", "--format=csv,noheader,nounits"])
    return [] if code != 0 or not out else [c.strip() for c in out.splitlines()[0].split(",")]


def ram_total_mb() -> int:
    if os.name == "nt":
        code, out = sh(["powershell", "-NoProfile", "-Command",
                        "[math]::Round((Get-CimInstance Win32_OperatingSystem)"
                        ".TotalVisibleMemorySize/1024)"])
        return int(out) if code == 0 and out.strip().isdigit() else 0
    try:  # Linux
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) // 1024
    except OSError:
        pass
    return 0


class GpuSampler(threading.Thread):
    """Sample clock, utilisation and throttle reasons WHILE the benchmark runs.

    A reading taken before the work started is a reading of an idle GPU, and the number that
    matters -- whether it holds its clock under sustained load -- is only visible during it.
    """

    def __init__(self, period: float = 2.0) -> None:
        super().__init__(daemon=True)
        self.period = period
        self.stop = threading.Event()
        self.clocks: list[int] = []
        self.utils: list[int] = []
        self.temps: list[int] = []
        self.throttles: set[str] = set()

    def run(self) -> None:
        while not self.stop.is_set():
            vals = nvidia("clocks.sm,utilization.gpu,temperature.gpu")
            if len(vals) == 3:
                for store, v in zip((self.clocks, self.utils, self.temps), vals):
                    if v.isdigit():
                        store.append(int(v))
            code, out = sh(["nvidia-smi",
                            "--query-gpu=clocks_throttle_reasons.sw_power_cap,"
                            "clocks_throttle_reasons.sw_thermal_slowdown,"
                            "clocks_throttle_reasons.hw_thermal_slowdown",
                            "--format=csv,noheader"])
            if code == 0 and out:
                names = ("sw_power_cap", "sw_thermal", "hw_thermal")
                for name, state in zip(names, [c.strip() for c in out.splitlines()[0].split(",")]):
                    if state.lower() == "active":
                        self.throttles.add(name)
            self.stop.wait(self.period)

    def summary(self) -> dict:
        def stat(xs):
            return {"min": min(xs), "max": max(xs), "mean": round(sum(xs) / len(xs), 1)} if xs else {}
        return {"sm_clock_mhz": stat(self.clocks), "utilisation_pct": stat(self.utils),
                "temperature_c": stat(self.temps), "throttled_by": sorted(self.throttles),
                "samples": len(self.clocks)}


def pick_profile(ram_mb: int, vram_mb: int) -> tuple[str, list[str]]:
    """The largest profile BOTH axes support, and every axis that disagreed."""
    notes: list[str] = []
    best = "laptop"
    for name in ("laptop", "workstation", "many_core"):
        need = PROFILE_NEEDS[name]
        ram_ok = ram_mb >= need["ram_gb"] * 1024 * 0.9   # 10% slack: reported RAM is never exact
        vram_ok = vram_mb >= need["vram_gb"] * 1024 * 0.9
        if ram_ok and vram_ok:
            best = name
        elif ram_ok and not vram_ok:
            notes.append(
                f"{name}: RAM is enough ({ram_mb} MB) but it assumes {need['vram_gb']} GB VRAM "
                f"and this card has {vram_mb} MB. Not chosen automatically -- picking on RAM "
                f"alone is how a benchmark becomes an out-of-memory error twenty minutes in."
            )
            # A refusal that leaves you with no next step is not advice. The shipped profiles
            # jump 8 GB/4 GB to 32 GB/12 GB with nothing between, so a 32 GB machine with an
            # 8 GB card falls in the gap and gets `laptop`, which under-uses it badly. The
            # reference laptop peaks at 1,882 MB of VRAM on `laptop`, so a card with more than
            # about 6 GB has real headroom and the bigger profile is worth TRYING -- it is a
            # measurement, not a leap, because `vram_peak_mb` in the output tells you whether
            # it fitted.
            notes.append(
                f"   try it anyway with --profile {name} and read vram_peak_mb: the reference "
                f"machine peaks at {REFERENCE['vram_peak_mb']} MB on `laptop`, so {vram_mb} MB "
                f"is unlikely to be the binding constraint. If it OOMs, that is a 3-minute "
                f"answer rather than a lost run."
            )
    return best, notes



def _config_with_workers(py: Path, root: Path, profile: str, workers: int, tmp: Path) -> Path:
    """A full config for `profile` with rollout.workers overridden.

    `royalelearn bench` takes a profile OR a config and has no worker flag, so the override has
    to go through a file. `royalelearn config` writes a fully populated one.
    """
    out = tmp / f"profile-{profile}-w{workers}.json"
    code, msg = sh([str(py), "-m", "royalelearn", "config", "--profile", profile, "-o", str(out)],
                   cwd=root / "RoyaleLearn")
    if code != 0 or not out.exists():
        raise RuntimeError(f"could not write a config: {msg[-300:]}")
    cfg = json.loads(out.read_text())
    cfg.setdefault("rollout", {})["workers"] = workers
    out.write_text(json.dumps(cfg, indent=2))
    return out


ENV_MS = re.compile(r"env_ms_per_game_step\s+([0-9.eE+-]+)")
UPD_TPS = re.compile(r"update_timesteps_per_second\s+([0-9.eE+-]+)")
def _time_block(text: str) -> dict:
    """The `time` section of the LAST iteration, as a dict.

    NOT a regex over the whole page. `iteration` appears under `run` as a COUNTER and under
    `time` as SECONDS, so a pattern matching the bare word finds both -- on the first real
    output I tried it returned ['1', '126.7', '2', '109.8'] and the correct value was last by
    luck. A parser that is right by accident on one sample is wrong on the next.
    """
    block, out = None, {}
    for line in text.splitlines():
        stripped = line.strip()
        if not line.startswith(" ") and stripped:
            block = None
        elif line[:4] == "  " + stripped[:2] and stripped and not line[:5].strip() and False:
            pass
        if stripped in ("run", "time", "ppo", "policy", "env", "ladder", "health", "throughput"):
            # section headers sit at two spaces of indent; their fields at four or more
            if len(line) - len(line.lstrip()) == 2:
                block = stripped
                continue
        if block == "time" and len(line) - len(line.lstrip()) >= 4:
            parts = stripped.split()
            if len(parts) == 2:
                try:
                    out[parts[0]] = float(parts[1])
                except ValueError:
                    pass
    return out


def run_sweep(py: Path, root: Path, profile: str, counts: list[int], iterations: int,
              seconds: float, tmp: Path) -> list[dict]:
    """One bench per worker count, reporting the per-step engine cost.

    WHY THIS EXISTS. A benchmark on an RTX 5050 put 48.5% of the iteration in the engine while
    the GPU idled at 68% utilisation, against 9.5% on the reference laptop -- and the per-step
    engine cost was 2.03x higher, which is the opposite of what better hardware should give.
    Two explanations have OPPOSITE consequences:

      contention or core scheduling   -- the per-step cost falls as workers drop, the engine is
                                         fine, and the fix is worker affinity
      intrinsic per-step cost         -- it stays flat, and on the hardware this project wants
                                         to scale to the engine is the dominant term

    `env_ms_per_game_step` is per game step, so it is comparable across worker counts in a way
    seconds-per-iteration is not. Read that column, not the wall clock.
    """
    out = []
    for n in counts:
        cfg = _config_with_workers(py, root, profile, n, tmp)
        print(f"\n--- workers={n} ---", flush=True)
        sampler = GpuSampler()
        sampler.start()
        code, text = sh([str(py), "-m", "royalelearn", "bench", "--config", str(cfg),
                         "--iterations", str(iterations), "--seconds", str(seconds)],
                        cwd=root / "RoyaleLearn", timeout=seconds * 6 + 900)
        sampler.stop.set(); sampler.join(timeout=10)
        env_ms = ENV_MS.search(text)
        tps = UPD_TPS.search(text)
        tb = _time_block(text)
        row = {
            "workers": n, "exit_code": code,
            "env_ms_per_game_step": float(env_ms.group(1)) if env_ms else None,
            "update_timesteps_per_second": float(tps.group(1)) if tps else None,
            "env_share_of_iteration": (tb["env"] / tb["iteration"]) if tb.get("iteration") else None,
            "gpu": sampler.summary(),
        }
        out.append(row)
        print("    env_ms_per_game_step %s  env share %s"
              % (row["env_ms_per_game_step"], row["env_share_of_iteration"]), flush=True)
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", type=Path, required=True)
    ap.add_argument("--profile", default=None, help="override the automatic choice")
    ap.add_argument("--iterations", type=int, default=3)
    ap.add_argument("--seconds", type=float, default=240.0)
    ap.add_argument("--out", type=Path, default=Path("hardware_bench.json"))
    ap.add_argument("--workers", type=int, default=None,
                    help="override rollout.workers (writes a temp config from the profile)")
    ap.add_argument("--sweep", default=None,
                    help="comma-separated worker counts, e.g. 1,2,3. Answers whether the engine "
                         "cost is intrinsic or contention.")
    args = ap.parse_args(argv)

    root = args.root.expanduser().resolve()
    py = root / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not py.exists():
        print(f"no venv at {py}. Run setup_workspace.py first.")
        return 2

    gpu = nvidia("name,memory.total,clocks.max.sm,compute_cap")
    vram_mb = int(gpu[1]) if len(gpu) > 1 and gpu[1].isdigit() else 0
    ram_mb = ram_total_mb()
    machine = {
        "gpu": gpu[0] if gpu else "none detected",
        "vram_total_mb": vram_mb,
        "max_sm_clock_mhz": int(gpu[2]) if len(gpu) > 2 and gpu[2].isdigit() else 0,
        "compute_capability": gpu[3] if len(gpu) > 3 else "",
        "ram_total_mb": ram_mb,
        "cpu": platform.processor() or platform.machine(),
        "cpu_count": os.cpu_count(),
        "platform": platform.platform(),
        "python": sys.version.split()[0],
    }
    auto, notes = pick_profile(ram_mb, vram_mb)
    profile = args.profile or auto

    print("MACHINE")
    for k, v in machine.items():
        print(f"  {k:24} {v}")
    print(f"\nPROFILE  {profile}" + ("" if args.profile else f"  (auto; largest both axes support)"))
    for n in notes:
        print(f"  note: {n}")

    if args.sweep:
        counts = [int(c) for c in args.sweep.split(",") if c.strip()]
        tmp = args.out.parent / "_sweep_configs"
        tmp.mkdir(parents=True, exist_ok=True)
        sweep = run_sweep(py, root, profile, counts, args.iterations, args.seconds, tmp)
        print()
        print("WORKER SWEEP -- is the engine cost intrinsic, or contention?")
        print("%-9s %-22s %-24s %-16s" % ("workers", "env_ms_per_game_step", "update_timesteps/s", "env share"))
        for r in sweep:
            print("%-9d %-22s %-24s %-16s" % (
                r["workers"], r["env_ms_per_game_step"], r["update_timesteps_per_second"],
                ("%.1f%%" % (100 * r["env_share_of_iteration"])) if r["env_share_of_iteration"] else "?"))
        vals = [r["env_ms_per_game_step"] for r in sweep if r["env_ms_per_game_step"]]
        if len(vals) > 1:
            lo, hi = min(vals), max(vals)
            print()
            if hi / lo >= 1.5:
                print("  per-step cost varies %.2fx across worker counts -> CONTENTION or core scheduling." % (hi / lo))
                print("  The engine is not the problem; worker affinity is. A slower engine stays affordable.")
            else:
                print("  per-step cost is flat within %.2fx across worker counts -> INTRINSIC." % (hi / lo))
                print("  On this hardware the engine is the dominant term and replacing it attacks the real cost.")
        args.out.write_text(json.dumps({"machine": machine, "profile": profile, "sweep": sweep,
                                        "reference": REFERENCE}, indent=2))
        print("\nwrote %s" % args.out)
        return 0

    print(f"\nrunning royalelearn bench, {args.iterations} iteration(s), sampling the GPU "
          f"throughout...", flush=True)
    sampler = GpuSampler()
    sampler.start()
    t0 = time.monotonic()
    code, out = sh([str(py), "-m", "royalelearn", "bench",
                    "--profile", profile,
                    "--iterations", str(args.iterations),
                    "--seconds", str(args.seconds)],
                   cwd=root / "RoyaleLearn", timeout=args.seconds * 6 + 900)
    wall = time.monotonic() - t0
    sampler.stop.set()
    sampler.join(timeout=10)
    gpu_summary = sampler.summary()

    print(out[-3000:] if out else "(no output)")
    result = {
        "machine": machine, "profile": profile, "profile_notes": notes,
        "bench_exit_code": code, "wall_seconds": round(wall, 1),
        "gpu_during_run": gpu_summary, "bench_stdout": out,
        "reference": REFERENCE,
    }
    args.out.write_text(json.dumps(result, indent=2))

    print("\nGPU DURING THE RUN  (a clock read at rest is not the clock the benchmark got)")
    for k, v in gpu_summary.items():
        print(f"  {k:24} {v}")
    if gpu_summary.get("throttled_by"):
        mx = machine["max_sm_clock_mhz"]
        held = gpu_summary.get("sm_clock_mhz", {}).get("mean", 0)
        pct = f"{100*held/mx:.0f}% of max" if mx else "?"
        print(f"  -> THROTTLED by {', '.join(gpu_summary['throttled_by'])}: held {held} MHz, {pct}.")
        print("     Sustained throughput will be below anything measured in the first minutes.")
    else:
        print("  -> no throttling seen; this machine held its clock for the whole benchmark.")

    print(f"\nREFERENCE  {REFERENCE['label']}")
    print(f"  {REFERENCE['seconds_per_iteration_cold']} s/iteration cold, "
          f"{REFERENCE['seconds_per_iteration_power_capped']} s/iteration once power-capped "
          f"({REFERENCE['profile']} profile, {REFERENCE['dtype']})")
    print(f"  critic pass {REFERENCE['critic_pass_seconds_cold']} s -> "
          f"{REFERENCE['critic_pass_seconds_power_capped']} s, same run, seven hours apart")
    print(f"  {REFERENCE['note']}")
    print(f"\nwrote {args.out}")
    return 0 if code == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
