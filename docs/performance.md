# Rendering computation: one worker versus multiple workers

The current tables and charts time only the rendering-computation phase. Camera and scene construction, normal/brightness precomputation, process startup, file I/O, terminal output, and hashing are outside the interval. Allocation inside `render()` and worker launch/join remain included. The [timing boundaries](timing.md) identify the exact start and stop points.

## Original testing

In the original bell-shaped visualization, Derek recalls a roughly **6–7× speedup with ten threads** at relatively high image resolution and triangle counts, with Activity Monitor’s CPU chart saturated. Exact workload dimensions, build flags, and timing logs have not been recovered. The [dedicated bell investigation](bell-performance.md) measures the archived `og_hat.cpp` eight-worker branch separately from that ten-thread historical account.

## Maintained renderer

![Rendering-computation time by worker count, with min–max whiskers](images/thread-scaling.png)

These fresh measurements use an Apple M4 (four performance cores, six efficiency cores), arm64, macOS 27.0.1; Apple clang 21.0.0 with `-O2 -std=c++17 -Wall -Wextra -Wpedantic -pthread`.

| Workers | 160×80, grid 20: median computation | Speedup | 640×320, grid 40: median computation | Speedup |
| --- | ---: | ---: | ---: | ---: |
| 1 | 0.050541 s | 1.00× | 3.134211 s | 1.00× |
| 2 | 0.024824 s | 2.04× | 1.814998 s | 1.73× |
| 4 | 0.014392 s | 3.51× | 1.172353 s | 2.67× |
| 8 | 0.012624 s | 4.00× | 0.842938 s | 3.72× |
| Auto (10) | 0.012245 s | 4.13× | 0.811318 s | 3.86× |

Grid 20 contains 800 triangles; grid 40 contains 3,200. Each setting received one warmup and five measured runs, interleaved in a deterministically shuffled order. Every image hash matched across worker counts, repetitions, and the earlier same-workload output.

The metric is elapsed `std::chrono::steady_clock` time immediately around `raytracer::render(...)`, before any PGM or ASCII output. The executable reports it as `render computation: ... seconds`. This is wall-clock duration for the relevant phase, not summed CPU time across threads. The benchmark uses only that field for medians, ranges, speedups, and chart bars. Whole-process time and the older broad internal timer are recorded only as diagnostics.

More workers helped in this session, with diminishing gains. Thread management, different core speeds, memory behavior, and scheduling can affect the result; these measurements do not isolate each contribution. Other desktop activity, thermal state, and power mode were not controlled. New ratios are fresh measurements: differences from the earlier publication values also reflect variation between sessions, not just a changed timer boundary.

## Reproduce

```sh
make -B CXX=c++ CXXFLAGS='-O2 -std=c++17 -Wall -Wextra -Wpedantic'
python3 scripts/benchmark.py --output /tmp/my-thread-compute.json
```

Measurement requires only Python’s standard library and the built executable. Each subprocess has a 120-second limit. To regenerate the published chart from the [computation record](benchmarks/thread-compute.json), install Matplotlib in an optional plotting environment and run:

```sh
python3 scripts/benchmark.py --chart docs/benchmarks/thread-compute.json
```

The raw record includes individual trials, warmups, computation and diagnostic times, min/median/max summaries, output hashes, compiler/build information, source/binary hashes, hardware, and UTC timestamps. Chart generation rejects older records without the computation metric rather than silently changing their labels.

## Original threading experiments

The small array-summing `experiments/multithread/threading.cpp` does not establish rendering performance: its unused result can be optimized away, its ordering is fixed, and it measures a different workload. The original bell and swirl renderers contain actual single/multithread paths. Their geometry and partitioning defects remain in the archive, so matching output does not establish geometric correctness.

The archived swirl comparison uses temporary copies of `experiments/multithread/render.cpp`: terminal display is disabled, and the single/multithread switch is toggled. Image mode produces 200×100 pixels and 800 triangles. A steady-clock timer is injected immediately before the dispatch branch and stopped before the text-output loop, with worker launch/join included. Original source files remain unchanged.

With `-O2 -std=c++17 -pthread`, one worker took a median **9.4902 s** (range 9.3109–9.5242); ten workers took **5.0087 s** (4.6419–5.4831), a **1.89×** computation speedup. Each setting received one warmup and three measured runs in shuffled paired order. All eight outputs matched each other and the earlier same-workload output. This is a different implementation and workload from the maintained sweep above.

```sh
python3 scripts/benchmark.py --legacy --rounds 3 --output /tmp/my-legacy-compute.json
```

The [fresh archival computation record](benchmarks/legacy-compute.json) records all trials, temporary instrumentation, source/build hashes, and diagnostic broader timings. Each process has a 60-second timeout.

## Earlier measurements

The earlier [maintained-renderer](benchmarks/thread-scaling.json), [bell](benchmarks/bell-scaling.json), and [archived swirl](benchmarks/legacy-renderer.json) records retain their original, broader timing scopes. They are archival records, not inputs to the current computation-only charts. Their setup or I/O durations were not estimated and subtracted after measurement.
