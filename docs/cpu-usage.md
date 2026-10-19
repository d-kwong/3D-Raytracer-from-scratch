# Checking actual CPU use

The original observation was a fully saturated CPU chart during rendering. Worker count and speedup alone cannot verify that observation, so this check measures the maintained renderer's actual CPU consumption during a sustained real render.

## What was measured

These measurements used the existing optimized C++ executable on an Apple M4 (4 performance cores, 6 efficiency cores), macOS 27.0.1, arm64. No extra busy loops, algorithm changes, affinity settings or artificial work were added.

| Real render | Wall time | User CPU time | System CPU time | Average process CPU | Peak sampled process CPU |
| --- | ---: | ---: | ---: | ---: | ---: |
| 640×320, grid 40, 1 worker | 3.193 s | 3.143 s | 0.021 s | 99.1% | 100.0% |
| 1600×800, grid 100, 10 workers | 34.573 s | 267.032 s | 2.034 s | 778.3% | 929.0% |

Here **100% means one fully occupied CPU core**; ten cores would be 1000%. Average process CPU is `100 × (user CPU seconds + system CPU seconds) / wall seconds`, using `os.wait4` resource usage for the renderer process and all its threads. The sustained render consumed 269.066 CPU-seconds in 34.573 elapsed seconds: an average of 7.78 occupied cores. This counts scheduled CPU time; it does not treat an efficiency core as equivalent to a performance core in rendering throughput.

The workloads differ, so this table is a utilization check, not a single-versus-multithread speedup comparison. The controlled same-workload timing comparisons are documented in [performance.md](performance.md) and [bell-performance.md](bell-performance.md).

## What Activity Monitor showed

During that same sustained run, the native Activity Monitor process row showed **821.2%** and later **811.5%**, with **11 threads** (ten rendering workers and the waiting main thread). Those are separate visual observations, rather than the profiler's full-run average or its peak.

The whole-machine CPU chart simultaneously showed **0.10% idle** and later **0.00% idle**. A fully saturated machine-wide chart and a renderer process below 1000% can occur together: the chart includes other processes, while the process row reports the renderer alone. The observed machine-wide user/system percentages were 96.27%/3.64% and 92.86%/7.14%, respectively; small sum discrepancies reflect display rounding. These snapshots were manually observed during the run, and the author independently confirmed seeing CPU usage pushed to the maximum this time. No Activity Monitor screenshot is included in the repository.

## Samples and the end of the run

`top` sampled the renderer roughly once per second. Its initial zero sample is retained but excluded from the peak. The largest later sample was **929.0% at 26.68 s**. There were ten rendering workers for most of the run, followed by a visible tail:

| Elapsed time | Sampled process CPU | Total process threads |
| --- | ---: | ---: |
| 26.68 s | 929.0% | 11 |
| 31.00 s | 762.3% | 10 |
| 32.07 s | 777.8% | 8 |
| 33.17 s | 683.5% | 8 |
| 34.22 s | 406.0% | 2 |

CPU percentages refer to sampling intervals, while thread counts reflect the displayed process state; a sample can include work from threads that finished during its interval.

The source assigns one contiguous pixel block to each worker and then joins them. The decreasing thread count establishes that some blocks finished earlier than others. Static partitioning, different core speeds, per-pixel work differences and operating-system scheduling are plausible contributors; this profile does not isolate their individual effects. Dynamic scheduling would need a separate implementation and controlled comparison before claiming an improvement.

The recorded run demonstrates substantial parallel CPU use and a fully busy machine chart, with a process peak near ten occupied cores. It does not demonstrate a renderer process remaining at 1000% throughout the run, and it does not reconstruct the original project's historical CPU measurements.

## Reproduce

Build with the normal Makefile defaults (`-O2 -std=c++17 -Wall -Wextra -Wpedantic`, linked with `-pthread`), then run:

```sh
make
python3 scripts/profile_cpu.py --width 640 --height 320 --grid 40 --threads 1 --timeout 15 --output /tmp/my-cpu-usage.json
python3 scripts/profile_cpu.py --width 1600 --height 800 --grid 100 --threads 10 --timeout 65 --pid-file /tmp/raytracer-cpu.pid --output /tmp/my-cpu-usage.json
```

The script requires Unix `os.wait4`; on macOS it also starts `top` for interval samples. macOS or a sandbox may require permission to inspect processes. If `top` is unavailable, the independent CPU-time measurement still works and the sampling limitation is recorded. It prints the renderer PID immediately, so Activity Monitor can be filtered to `raytracer` while the longer job runs. A timeout stops the real rendering process and records the unsuccessful run.

Each job writes a temporary PGM, hashes it on success and removes temporary files afterward. Build time, the profiler's CPU use, Activity Monitor and `top` CPU use are excluded from the renderer's resource-usage total. The wall timer includes process startup, scene construction, rendering and output writing, with up to roughly 25 ms of completion-polling delay. Sampling intervals, other system activity, thermal conditions and core scheduling affect observations; one run is diagnostic rather than a universal utilization guarantee.

The [raw record](benchmarks/cpu-usage.json) preserves resource usage, every `top` sample, binary identity, hardware metadata, settings, UTC timestamps and the separately recorded Activity Monitor observations.
