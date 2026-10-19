#!/usr/bin/env python3
"""Measure actual renderer CPU time and macOS top samples; no synthetic workload."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import tempfile
import threading
import time

from benchmark import machine_info

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--width", type=int, default=1600)
    parser.add_argument("--height", type=int, default=800)
    parser.add_argument("--grid", type=int, default=100)
    parser.add_argument("--threads", type=int, default=10)
    parser.add_argument("--timeout", type=float, default=75)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/benchmarks/cpu-usage.json")
    parser.add_argument("--pid-file", type=Path, help="Write live renderer PID for Activity Monitor")
    args = parser.parse_args()
    binary = ROOT / "build/raytracer"
    if not hasattr(os, "wait4"):
        parser.error("This profiler requires os.wait4 (Unix process resource usage).")
    if not binary.is_file():
        parser.error("Build build/raytracer with make first.")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    record = {"started_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "machine": machine_info(), "binary_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
              "width": args.width, "height": args.height, "grid": args.grid,
              "triangles": 2 * args.grid * args.grid, "requested_workers": args.threads,
              "cpu_time_source": "os.wait4 rusage.ru_utime + rusage.ru_stime, renderer process only",
              "cpu_percent_convention": "100% = one fully occupied CPU core; 1000% = ten",
              "top_command": "top -l 0 -s 1 -pid PID -stats pid,cpu,time,threads",
              "top_samples": []}
    sample_process = None
    sample_thread = None
    samples = record["top_samples"]
    with tempfile.TemporaryDirectory(prefix="raytracer-cpu-") as directory:
        working = Path(directory)
        output = working / "render.pgm"
        command = [str(binary), "--width", str(args.width), "--height", str(args.height),
                   "--grid", str(args.grid), "--threads", str(args.threads), "--output", str(output)]
        with (working / "stderr.txt").open("w") as stderr:
            start = time.perf_counter()
            process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=stderr)
            print(f"Renderer PID {process.pid}; {args.width}x{args.height}, grid {args.grid}, workers {args.threads}", flush=True)
            if args.pid_file:
                args.pid_file.write_text(str(process.pid) + "\n")
            if platform.system() == "Darwin":
                try:
                    sample_process = subprocess.Popen(["top", "-l", "0", "-s", "1", "-pid", str(process.pid),
                                                       "-stats", "pid,cpu,time,threads"], stdout=subprocess.PIPE,
                                                      stderr=subprocess.PIPE, text=True, bufsize=1)
                    def collect():
                        for line in sample_process.stdout:
                            match = re.match(r"\s*(\d+)\s+([\d.]+)\s+(\S+)\s+(\S+)", line)
                            if match and int(match[1]) == process.pid:
                                samples.append({"elapsed_seconds": time.perf_counter()-start,
                                                "cpu_percent": float(match[2]), "cpu_time_display": match[3],
                                                "threads_display": match[4],
                                                "initial_top_sample": len(samples) == 0})
                    sample_thread = threading.Thread(target=collect, daemon=True)
                    sample_thread.start()
                except OSError as error:
                    record["top_error"] = type(error).__name__
            while True:
                waited, status, usage = os.wait4(process.pid, os.WNOHANG)
                if waited:
                    process.returncode = os.waitstatus_to_exitcode(status)
                    elapsed = time.perf_counter()-start
                    break
                if time.perf_counter()-start > args.timeout:
                    process.kill()
                    waited, status, usage = os.wait4(process.pid, 0)
                    process.returncode = os.waitstatus_to_exitcode(status)
                    elapsed = time.perf_counter()-start
                    record["timeout"] = True
                    break
                time.sleep(0.025)
            if sample_process:
                if sample_process.poll() is None:
                    sample_process.terminate()
                sample_process.wait(timeout=5)
                sample_thread.join(timeout=5)
                errors = sample_process.stderr.read().strip()
                if errors:
                    record["top_error"] = errors
        record.update(exit_code=process.returncode, wall_seconds=elapsed,
                      user_cpu_seconds=usage.ru_utime, system_cpu_seconds=usage.ru_stime)
        cpu_seconds = usage.ru_utime + usage.ru_stime
        record["total_cpu_seconds"] = cpu_seconds
        record["average_utilized_cores"] = cpu_seconds / elapsed
        record["average_cpu_percent"] = 100 * cpu_seconds / elapsed
        measured_samples = [s for s in samples if not s["initial_top_sample"]]
        if measured_samples:
            record["peak_sampled_cpu_percent"] = max(s["cpu_percent"] for s in measured_samples)
        if process.returncode == 0:
            record["output_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
            summary = re.search(r"(\d+) workers;.* in ([\d.eE+-]+) seconds", (working / "stderr.txt").read_text())
            if summary:
                record["actual_workers"] = int(summary[1])
                record["renderer_internal_seconds"] = float(summary[2])
        record["finished_utc"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    if args.output.exists():
        result = json.loads(args.output.read_text())
    else:
        result = {"method": "Real renderer processes only. CPU-time ratio includes startup, scene construction, render and PGM output. top sampling runs separately and is excluded from renderer rusage.", "runs": []}
    result["runs"].append(record)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(f"Wall {elapsed:.3f}s; renderer CPU {cpu_seconds:.3f}s; average {record['average_cpu_percent']:.1f}% ({record['average_utilized_cores']:.2f} cores); samples {len(samples)}", flush=True)
    if process.returncode:
        raise SystemExit(process.returncode)


if __name__ == "__main__":
    main()
