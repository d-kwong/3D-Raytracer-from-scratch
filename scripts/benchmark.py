#!/usr/bin/env python3
"""Compare renderer worker counts. Measurements use only Python's standard library.

Optional chart creation requires Matplotlib: python3 scripts/benchmark.py --chart results.json
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import random
import re
import statistics
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
WORKLOADS = [("Quick start", 160, 80, 20), ("Larger render", 640, 320, 40)]


def command_output(command):
    try:
        return subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def machine_info():
    info = {"os": platform.system(), "os_version": platform.mac_ver()[0] or platform.release(),
            "architecture": platform.machine(), "logical_cpus": os.cpu_count()}
    if platform.system() == "Darwin":
        for field, key in [("cpu", "machdep.cpu.brand_string"), ("physical_cpus", "hw.physicalcpu"),
                           ("performance_cores", "hw.perflevel0.physicalcpu"),
                           ("efficiency_cores", "hw.perflevel1.physicalcpu")]:
            value = command_output(["sysctl", "-n", key])
            info[field] = int(value) if value and value.isdigit() else value
    return info


def run_benchmarks(args):
    binary = ROOT / "build/raytracer"
    if not binary.is_file():
        raise SystemExit("Build first with make; build/raytracer was not found.")
    workers = [(str(n), n) for n in (1, 2, 4, 8)]
    automatic = os.cpu_count() or 1
    if automatic not in (1, 2, 4, 8):
        workers.append(("auto", 0))
    compiler = command_output([os.environ.get("CXX", "c++"), "--version"])
    result = {"started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "machine": machine_info(), "compiler": compiler.splitlines()[0] if compiler else None,
              "build_command": args.build_command, "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
              "method": {"clock": "time.perf_counter", "timing": "subprocess start through exit, including scene construction, rendering, PGM output and startup",
                         "warmups_per_configuration": 1, "rounds": args.rounds, "shuffle_seed": args.seed,
                         "order": "one warmup per configuration, then interleaved rounds; configurations shuffled each round",
                         "checksum_timing": "after timing, excluded from wall_seconds"}, "workloads": []}
    rng = random.Random(args.seed)
    with tempfile.TemporaryDirectory(prefix="raytracer-benchmark-") as directory:
        for title, width, height, grid in WORKLOADS:
            workload = {"name": title, "width": width, "height": height, "grid": grid,
                        "triangles": 2 * grid * grid, "runs": [], "summary": []}
            expected_hash = None
            for round_number in range(args.rounds + 1):
                order = workers.copy()
                rng.shuffle(order)
                for label, requested in order:
                    output = Path(directory) / "render.pgm"
                    command = [str(binary), "--width", str(width), "--height", str(height), "--grid", str(grid),
                               "--threads", str(requested), "--output", str(output)]
                    start = time.perf_counter()
                    completed = subprocess.run(command, check=True, capture_output=True, text=True, timeout=120)
                    elapsed = time.perf_counter() - start
                    digest = hashlib.sha256(output.read_bytes()).hexdigest()
                    if expected_hash is not None and digest != expected_hash:
                        raise RuntimeError("Image mismatch between worker configurations or repetitions")
                    expected_hash = digest
                    match = re.search(r"(\d+) workers;.* in ([\d.eE+-]+) seconds", completed.stderr)
                    if not match:
                        raise RuntimeError("Could not parse renderer worker count/timing")
                    run = {"round": round_number, "warmup": round_number == 0, "configuration": label,
                           "requested_threads": requested, "actual_workers": int(match[1]),
                           "wall_seconds": elapsed, "renderer_seconds": float(match[2]), "pgm_sha256": digest}
                    workload["runs"].append(run)
                    print(f"{title}: {'warmup' if round_number == 0 else f'round {round_number}'} / {label}: {elapsed:.4f}s", flush=True)
            for label, requested in workers:
                runs = [r for r in workload["runs"] if not r["warmup"] and r["configuration"] == label]
                values = [r["wall_seconds"] for r in runs]
                workload["summary"].append({"configuration": label, "actual_workers": runs[0]["actual_workers"],
                                            "median_seconds": statistics.median(values), "min_seconds": min(values),
                                            "max_seconds": max(values)})
            baseline = workload["summary"][0]["median_seconds"]
            for entry in workload["summary"]:
                entry["speedup_vs_one"] = baseline / entry["median_seconds"]
            workload["all_images_identical"] = True
            workload["pgm_sha256"] = expected_hash
            result["workloads"].append(workload)
    result["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Saved {args.output}")


def run_legacy(args):
    source = (ROOT / "experiments/multithread/render.cpp").read_text()
    compiler = command_output(["c++", "--version"])
    result = {"started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "machine": machine_info(), "compiler_flags": "-O2 -std=c++17 -pthread",
              "compiler": compiler.splitlines()[0] if compiler else None,
              "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
              "source": "experiments/multithread/render.cpp", "width": 200, "height": 100, "grid": 20,
              "pixel_count": 20000, "multi_workers": os.cpu_count() or 0,
              "method": {"rounds": args.rounds, "warmups_per_configuration": 1,
                         "shuffle_seed": args.seed, "timing": "subprocess start through exit including original text pixel output",
                         "substitutions": ["paint_in_terminal = false", "multithread = true / false"],
                         "note": "Temporary builds; archive unchanged. This retains known geometry and thread-remainder defects."},
              "runs": []}
    rng = random.Random(args.seed)
    hashes = set()
    with tempfile.TemporaryDirectory(prefix="raytracer-legacy-benchmark-") as directory:
        working = Path(directory)
        for label, enabled in [("single", "false"), ("multi", "true")]:
            variant = source.replace("bool multithread = true;", f"bool multithread = {enabled};").replace("bool paint_in_terminal = true;", "bool paint_in_terminal = false;")
            cpp = working / f"{label}.cpp"
            cpp.write_text(variant)
            subprocess.run(["c++", "-O2", "-std=c++17", "-pthread", str(cpp), "-o", str(working / label)], check=True)
        for round_number in range(args.rounds + 1):
            order = ["single", "multi"]
            rng.shuffle(order)
            for label in order:
                start = time.perf_counter()
                completed = subprocess.run([str(working / label)], cwd=working, check=True, capture_output=True, text=True, timeout=60)
                elapsed = time.perf_counter() - start
                dimensions = re.search(r"image dimensions: (\d+)x(\d+)", completed.stdout)
                if not dimensions or dimensions.groups() != ("200", "100"):
                    raise RuntimeError("Unexpected legacy image dimensions")
                if len((working / "output.txt").read_text().split()) != 20000:
                    raise RuntimeError("Unexpected legacy pixel count")
                digest = hashlib.sha256((working / "output.txt").read_bytes()).hexdigest()
                hashes.add(digest)
                result["runs"].append({"round": round_number, "warmup": round_number == 0,
                                       "configuration": label, "wall_seconds": elapsed, "output_sha256": digest})
                print(f"Legacy: round {round_number} / {label}: {elapsed:.4f}s", flush=True)
        result["summary"] = []
        for label in ("single", "multi"):
            times = [r["wall_seconds"] for r in result["runs"] if not r["warmup"] and r["configuration"] == label]
            result["summary"].append({"configuration": label, "median_seconds": statistics.median(times),
                                      "min_seconds": min(times), "max_seconds": max(times)})
        result["summary"][1]["speedup_vs_single"] = result["summary"][0]["median_seconds"] / result["summary"][1]["median_seconds"]
    result["all_images_identical"] = len(hashes) == 1
    result["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    if len(hashes) != 1:
        raise SystemExit("Legacy pixel outputs differed; see saved results. No equal-output speedup claim is valid.")


def chart(input_path, output_path):
    # Optional dependency is isolated from the measurement path.
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    result = json.loads(input_path.read_text())
    hardware = result["machine"]
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 11,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.spines.left": False, "figure.facecolor": "#f5f3ee",
                         "axes.facecolor": "#f5f3ee", "text.color": "#202c36",
                         "axes.labelcolor": "#202c36", "xtick.color": "#56616a",
                         "ytick.color": "#202c36"}):
        fig, axes = plt.subplots(1, 2, figsize=(13.5, 6.3))
        fig.suptitle("More workers, same image", fontsize=25, x=0.06, ha="left", y=0.98)
        fig.text(0.06, 0.88, f"{hardware.get('cpu') or hardware['architecture']} · {hardware['logical_cpus']} CPU cores · median of {result['method']['rounds']} runs", color="#56616a", fontsize=12)
        for axis, workload in zip(axes, result["workloads"]):
            rows = workload["summary"]
            values = [r["median_seconds"] for r in rows]
            errors = [[r["median_seconds"] - r["min_seconds"] for r in rows],
                      [r["max_seconds"] - r["median_seconds"] for r in rows]]
            labels = [str(r["actual_workers"]) + (" (auto)" if r["configuration"] == "auto" else "") for r in rows]
            axis.barh(range(len(rows)), values, xerr=errors, height=0.55,
                      color=["#8598a0"] + ["#286a87"] * (len(rows)-1),
                      error_kw={"elinewidth": 1.3, "capsize": 4, "ecolor": "#202c36"})
            axis.set_yticks(range(len(rows)), labels)
            axis.invert_yaxis()
            axis.set_title(f"{workload['name']}\n{workload['width']} × {workload['height']} pixels · {workload['triangles']:,} triangles", loc="left", fontsize=13, pad=16)
            axis.set_xlabel("End-to-end wall time (seconds) ↓", labelpad=12)
            axis.set_ylabel("CPU workers")
            maximum = max(r["max_seconds"] for r in rows)
            axis.set_xlim(0, maximum * 1.45)
            axis.grid(axis="x", alpha=0.13)
            axis.set_axisbelow(True)
            axis.tick_params(axis="y", length=0)
            for index, row in enumerate(rows):
                axis.text(row["max_seconds"] + maximum * 0.035, index,
                          f"{row['median_seconds']:.3f}s  ·  {row['speedup_vs_one']:.2f}×", va="center", fontsize=10)
        fig.subplots_adjust(left=0.075, right=0.98, top=0.73, bottom=0.22, wspace=0.3)
        fig.text(0.06, 0.095, "Bars: medians · whiskers: min–max · speedup relative to one worker", fontsize=11)
        fig.text(0.06, 0.045, "One machine, one session; startup, scene construction and PGM writing included. Output hashes matched.", fontsize=10, color="#56616a")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=180, facecolor=fig.get_facecolor())
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Result JSON; defaults to a separate filename for each mode")
    parser.add_argument("--rounds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=20261019)
    parser.add_argument("--build-command", default="make -B CXX=c++ CXXFLAGS='-O2 -std=c++17 -Wall -Wextra -Wpedantic'")
    parser.add_argument("--chart", type=Path, help="Create chart from existing JSON; no measurements")
    parser.add_argument("--legacy", action="store_true", help="Benchmark temporary single/multi builds of the archived renderer")
    parser.add_argument("--chart-output", type=Path, default=ROOT / "docs/images/thread-scaling.png")
    args = parser.parse_args()
    if args.output is None:
        args.output = ROOT / "docs/benchmarks" / ("legacy-renderer.json" if args.legacy else "thread-scaling.json")
    if args.rounds < 1:
        parser.error("--rounds must be positive")
    if args.chart:
        chart(args.chart, args.chart_output)
    elif args.legacy:
        run_legacy(args)
    else:
        run_benchmarks(args)


if __name__ == "__main__":
    main()
