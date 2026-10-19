#!/usr/bin/env python3
"""Time temporary builds of the original cosine-bell renderer; archive unchanged."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import tempfile
import time

from benchmark import machine_info, instrument_compute_timer, parse_compute, COMPUTE_TIMER_START, COMPUTE_TIMER_STOP

ROOT = Path(__file__).resolve().parents[1]


def plot_results(input_path, output_path):
    result = json.loads(input_path.read_text())
    if result.get("metric") != "compute_seconds":
        raise SystemExit("Chart requires metric=compute_seconds; old timings cannot be relabeled.")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    sessions = [s for s in result["sessions"] if not s["calibration"]]
    if len(sessions) != 2:
        raise SystemExit("Chart expects the two recorded representative sessions; select a JSON with those sessions.")
    if any("compute_seconds" not in run for session in sessions for run in session["runs"]):
        raise SystemExit("Chart requires actual per-run computation samples.")
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.facecolor": "#f5f3ee", "axes.facecolor": "#f5f3ee"}):
        fig, axes = plt.subplots(1, 2, figsize=(12, 5.4))
        fig.suptitle("Original bell: computation only", x=0.07, y=0.98, ha="left", fontsize=23)
        for axis, session in zip(axes, sessions):
            rows = session["summary"]
            values = [r["compute_seconds"]["median"] for r in rows]
            errors = [[r["compute_seconds"]["median"]-r["compute_seconds"]["min"] for r in rows],
                      [r["compute_seconds"]["max"]-r["compute_seconds"]["median"] for r in rows]]
            axis.bar(["1 worker", "8 workers"], values, yerr=errors, capsize=6, width=0.5, color=["#8598a0", "#286a87"])
            axis.set_title(f"-{rows[0]['optimization']} · {session['width']} × {session['height']} pixels\n{session['triangles']:,} triangles · original fixed eight workers", loc="left", fontsize=12, pad=15)
            axis.set_ylabel("Rendering computation (seconds) ↓")
            axis.set_ylim(0, max(r["compute_seconds"]["max"] for r in rows)*1.28)
            axis.grid(axis="y", alpha=0.15)
            axis.set_axisbelow(True)
            for index, row in enumerate(rows):
                axis.text(index, row["compute_seconds"]["max"]+max(values)*0.035,
                          f"{row['compute_seconds']['median']:.2f}s · {row['compute_speedup_vs_one']:.2f}×", ha="center")
        fig.subplots_adjust(left=0.075, right=0.97, top=0.71, bottom=0.25, wspace=0.3)
        hardware = ", ".join(sorted({s["machine"].get("cpu") or s["machine"]["architecture"] for s in sessions}))
        counts = {s["measured_rounds"] for s in sessions}
        repetitions = f"median of {next(iter(counts))} runs" if len(counts) == 1 else "medians of recorded runs"
        fig.text(0.07, 0.13, f"{hardware} · {repetitions} · whiskers show min–max · each pair produced identical output", fontsize=10)
        fig.text(0.07, 0.065, "Render dispatch only, including launch/join; scene, pixel-buffer setup, startup and output excluded.", fontsize=10, color="#56616a")
        fig.text(0.07, 0.018, "Workloads differ between panels; compare workers within each. Original build settings remain unknown.", fontsize=9, color="#56616a")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(output_path, dpi=180)
        plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--calibrate", action="store_true")
    parser.add_argument("--width", type=int, default=120)
    parser.add_argument("--grid", type=int, default=12)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--optimizations", nargs="+", choices=("O0", "O2"), default=["O0", "O2"])
    parser.add_argument("--preview", type=Path, help="Save the actual final output as a binary grayscale PGM")
    parser.add_argument("--chart", action="store_true", help="Create chart from existing JSON; requires Matplotlib")
    parser.add_argument("--chart-output", type=Path, default=ROOT / "docs/images/bell-compute-scaling.png")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/benchmarks/bell-compute.json")
    args = parser.parse_args()
    if args.chart:
        plot_results(args.output, args.chart_output)
        return
    if args.width < 4 or args.width % 4 or args.grid < 1 or args.rounds < 1:
        parser.error("width must be a positive multiple of four; grid and rounds must be positive")
    width, grid = (96, 12) if args.calibrate else (args.width, args.grid)
    height = width // 2
    source = (ROOT / "experiments/multithread/og_hat.cpp").read_text()
    compiler = subprocess.check_output(["c++", "--version"], text=True).splitlines()[0]
    if args.output.exists():
        result = json.loads(args.output.read_text())
        if result.get("metric") != "compute_seconds":
            parser.error("Refusing to append compute measurements to an old timing record")
    else:
        result = {"metric": "compute_seconds", "source": "experiments/multithread/og_hat.cpp",
                  "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                  "machine": machine_info(),
                  "compiler": compiler,
                  "method": {"flags": "-O0 / -O2 -std=c++17 -pthread", "workers": [1, 8],
                             "temporary_substitutions_only": ["multithread", "n_pixels_w", "n_faces"],
                             "compute_timer": "steady_clock immediately before dispatch if/else after pixel_colors allocation, stopped immediately after dispatch before output loop",
                             "timer_start_injection": COMPUTE_TIMER_START, "timer_stop_injection": COMPUTE_TIMER_STOP,
                             "scene": "original cosine bell, camera and light unchanged; terminal display remains false",
                             "wall_timer": "diagnostic ONLY: perf_counter subprocess launch through exit; output hashing excluded; not used for speedup",
                             "internal_timer": "diagnostic ONLY: original processing time printed by og_hat.cpp; excludes scene construction, includes pixel text writing; not used for speedup",
                             "warmups_per_measured_configuration": 1,
                             "order": "paired single/multi runs; order reversed on alternate rounds; optimization order reversed on alternate rounds"},
                  "sessions": []}
    session = {"calibration": args.calibrate, "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "machine": machine_info(), "compiler": compiler,
               "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
               "optimization_settings": args.optimizations, "measured_rounds": 1 if args.calibrate else args.rounds,
               "width": width, "height": height, "grid": grid, "triangles": 2 * grid * grid,
               "temporary_builds": [], "runs": [], "summary": []}
    try:
        with tempfile.TemporaryDirectory(prefix="raytracer-bell-") as directory:
            working = Path(directory)
            for optimization in args.optimizations:
                for workers in (1, 8):
                    modified = source.replace("bool multithread = true;", f"bool multithread = {'true' if workers == 8 else 'false'};")
                    modified = modified.replace("n_pixels_w = 200;", f"n_pixels_w = {width};").replace("n_faces = 10;", f"n_faces = {grid};")
                    modified = instrument_compute_timer(modified)
                    cpp = working / f"{optimization}-{workers}.cpp"
                    cpp.write_text(modified)
                    subprocess.run(["c++", f"-{optimization}", "-std=c++17", "-pthread", str(cpp), "-o", str(cpp.with_suffix(""))], check=True)
                    session["temporary_builds"].append({"optimization": optimization, "workers": workers,
                                                        "instrumented_source_sha256": hashlib.sha256(modified.encode()).hexdigest(),
                                                        "binary_sha256": hashlib.sha256(cpp.with_suffix("").read_bytes()).hexdigest()})
            hashes = set()
            rounds = [1] if args.calibrate else range(args.rounds + 1)
            for round_number in rounds:
                optimizations = args.optimizations if round_number % 2 == 0 else list(reversed(args.optimizations))
                for optimization in optimizations:
                    for workers in ([1, 8] if round_number % 2 == 0 else [8, 1]):
                        start = time.perf_counter()
                        completed = subprocess.run([str(working / f"{optimization}-{workers}")], cwd=working,
                                                   check=True, capture_output=True, text=True, timeout=60)
                        elapsed = time.perf_counter() - start
                        output = (working / "output.txt").read_bytes()
                        if len(output.split()) != width * height:
                            raise RuntimeError("Pixel count mismatch")
                        dimensions = re.search(r"image dimensions: (\d+)x(\d+)", completed.stdout)
                        if not dimensions or tuple(map(int, dimensions.groups())) != (width, height):
                            raise RuntimeError("Image dimensions mismatch")
                        timer = re.search(r"\nprocessing time: ([\d.eE+-]+) seconds", completed.stdout)
                        compute = parse_compute(completed.stderr)
                        digest = hashlib.sha256(output).hexdigest()
                        hashes.add(digest)
                        session["runs"].append({"round": round_number, "warmup": round_number == 0,
                                                "optimization": optimization, "workers": workers,
                                                "compute_seconds": compute, "wall_seconds": elapsed, "internal_seconds": float(timer[1]),
                                                "output_sha256": digest})
                        print(f"{'Calibration' if args.calibrate else f'Round {round_number}'} {optimization}/{workers} workers: compute {compute:.6f}s (wall {elapsed:.4f}s)", flush=True)
            if len(hashes) != 1:
                raise RuntimeError("Output hashes differ across optimization/worker settings")
            session["all_outputs_identical"] = True
            historical = json.loads((ROOT / "docs/benchmarks/bell-scaling.json").read_text())
            previous = next((s for s in historical["sessions"] if (s["width"],s["height"],s["grid"]) == (width,height,grid)), None)
            if previous is not None:
                if hashes != {r["output_sha256"] for r in previous["runs"]}:
                    raise RuntimeError("Bell output differs from historical same-workload output")
                session["matches_historical_output"] = True
                session["historical_reference"] = "docs/benchmarks/bell-scaling.json"
            if args.preview:
                args.preview.parent.mkdir(parents=True, exist_ok=True)
                pixels = bytes(round(max(0.0, min(1.0, float(value))) * 255) for value in output.split())
                args.preview.write_bytes(f"P5\n{width} {height}\n255\n".encode() + pixels)
            for optimization in args.optimizations:
                for workers in (1, 8):
                    runs = [r for r in session["runs"] if not r["warmup"] and r["optimization"] == optimization and r["workers"] == workers]
                    row = {"optimization": optimization, "workers": workers}
                    for key in ("compute_seconds", "wall_seconds", "internal_seconds"):
                        values = [r[key] for r in runs]
                        row[key] = {"median": statistics.median(values), "min": min(values), "max": max(values)}
                    session["summary"].append(row)
            for row in session["summary"]:
                baseline = next(r for r in session["summary"] if r["optimization"] == row["optimization"] and r["workers"] == 1)
                row["compute_speedup_vs_one"] = baseline["compute_seconds"]["median"] / row["compute_seconds"]["median"]
    finally:
        session["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        result["sessions"].append(session)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
