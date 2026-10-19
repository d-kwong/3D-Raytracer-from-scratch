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

from benchmark import machine_info

ROOT = Path(__file__).resolve().parents[1]


def plot_results(input_path, output_path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    result = json.loads(input_path.read_text())
    sessions = [s for s in result["sessions"] if not s["calibration"]]
    if len(sessions) != 2:
        raise SystemExit("Chart expects the two recorded representative sessions; select a JSON with those sessions.")
    with plt.rc_context({"font.family": "DejaVu Sans", "font.size": 11, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.facecolor": "#f5f3ee", "axes.facecolor": "#f5f3ee"}):
        fig, axes = plt.subplots(1, 2, figsize=(12, 5.4))
        fig.suptitle("Revisiting the original cosine bell", x=0.07, y=0.98, ha="left", fontsize=23)
        for axis, session in zip(axes, sessions):
            rows = session["summary"]
            values = [r["wall_seconds"]["median"] for r in rows]
            errors = [[r["wall_seconds"]["median"]-r["wall_seconds"]["min"] for r in rows],
                      [r["wall_seconds"]["max"]-r["wall_seconds"]["median"] for r in rows]]
            axis.bar(["1 worker", "8 workers"], values, yerr=errors, capsize=6, width=0.5, color=["#8598a0", "#286a87"])
            axis.set_title(f"-{rows[0]['optimization']} · {session['width']} × {session['height']} pixels\n{session['triangles']:,} triangles · original fixed eight workers", loc="left", fontsize=12, pad=15)
            axis.set_ylabel("End-to-end wall time (seconds) ↓")
            axis.set_ylim(0, max(r["wall_seconds"]["max"] for r in rows)*1.28)
            axis.grid(axis="y", alpha=0.15)
            axis.set_axisbelow(True)
            for index, row in enumerate(rows):
                axis.text(index, row["wall_seconds"]["max"]+max(values)*0.035,
                          f"{row['wall_seconds']['median']:.2f}s · {row['wall_speedup_vs_one']:.2f}×", ha="center")
        fig.subplots_adjust(left=0.075, right=0.97, top=0.71, bottom=0.25, wspace=0.3)
        fig.text(0.07, 0.13, "Apple M4 · median of three runs · whiskers show min–max · each pair produced identical output", fontsize=10)
        fig.text(0.07, 0.065, "Workloads differ between panels. Compare workers within each panel; original build settings are unknown.", fontsize=10, color="#56616a")
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
    parser.add_argument("--chart-output", type=Path, default=ROOT / "docs/images/bell-thread-scaling.png")
    parser.add_argument("--output", type=Path, default=ROOT / "docs/benchmarks/bell-scaling.json")
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
    else:
        result = {"source": "experiments/multithread/og_hat.cpp",
                  "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
                  "machine": machine_info(),
                  "compiler": compiler,
                  "method": {"flags": "-O0 / -O2 -std=c++17 -pthread", "workers": [1, 8],
                             "temporary_substitutions_only": ["multithread", "n_pixels_w", "n_faces"],
                             "scene": "original cosine bell, camera and light unchanged; terminal display remains false",
                             "wall_timer": "perf_counter subprocess launch through exit; output hashing excluded",
                             "internal_timer": "original processing time printed by og_hat.cpp; excludes scene construction, includes pixel text writing",
                             "warmups_per_measured_configuration": 1,
                             "order": "paired single/multi runs; order reversed on alternate rounds; optimization order reversed on alternate rounds"},
                  "sessions": []}
    session = {"calibration": args.calibrate, "started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "machine": machine_info(), "compiler": compiler,
               "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
               "optimization_settings": args.optimizations, "measured_rounds": 1 if args.calibrate else args.rounds,
               "width": width, "height": height, "grid": grid, "triangles": 2 * grid * grid,
               "runs": [], "summary": []}
    try:
        with tempfile.TemporaryDirectory(prefix="raytracer-bell-") as directory:
            working = Path(directory)
            for optimization in args.optimizations:
                for workers in (1, 8):
                    modified = source.replace("bool multithread = true;", f"bool multithread = {'true' if workers == 8 else 'false'};")
                    modified = modified.replace("n_pixels_w = 200;", f"n_pixels_w = {width};").replace("n_faces = 10;", f"n_faces = {grid};")
                    cpp = working / f"{optimization}-{workers}.cpp"
                    cpp.write_text(modified)
                    subprocess.run(["c++", f"-{optimization}", "-std=c++17", "-pthread", str(cpp), "-o", str(cpp.with_suffix(""))], check=True)
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
                        digest = hashlib.sha256(output).hexdigest()
                        hashes.add(digest)
                        session["runs"].append({"round": round_number, "warmup": round_number == 0,
                                                "optimization": optimization, "workers": workers,
                                                "wall_seconds": elapsed, "internal_seconds": float(timer[1]),
                                                "output_sha256": digest})
                        print(f"{'Calibration' if args.calibrate else f'Round {round_number}'} {optimization}/{workers} workers: wall {elapsed:.4f}s; internal {timer[1]}s", flush=True)
            if len(hashes) != 1:
                raise RuntimeError("Output hashes differ across optimization/worker settings")
            session["all_outputs_identical"] = True
            if args.preview:
                args.preview.parent.mkdir(parents=True, exist_ok=True)
                pixels = bytes(round(max(0.0, min(1.0, float(value))) * 255) for value in output.split())
                args.preview.write_bytes(f"P5\n{width} {height}\n255\n".encode() + pixels)
            for optimization in args.optimizations:
                for workers in (1, 8):
                    runs = [r for r in session["runs"] if not r["warmup"] and r["optimization"] == optimization and r["workers"] == workers]
                    row = {"optimization": optimization, "workers": workers}
                    for key in ("wall_seconds", "internal_seconds"):
                        values = [r[key] for r in runs]
                        row[key] = {"median": statistics.median(values), "min": min(values), "max": max(values)}
                    session["summary"].append(row)
            for row in session["summary"]:
                baseline = next(r for r in session["summary"] if r["optimization"] == row["optimization"] and r["workers"] == 1)
                row["wall_speedup_vs_one"] = baseline["wall_seconds"]["median"] / row["wall_seconds"]["median"]
                row["internal_speedup_vs_one"] = baseline["internal_seconds"]["median"] / row["internal_seconds"]["median"]
    finally:
        session["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        result["sessions"].append(session)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
