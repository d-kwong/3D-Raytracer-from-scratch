# Revisiting the original bell-surface timing

The remembered 6–7× improvement came from a 3D bell visualization with substantial pixel and triangle counts. Derek subsequently clarified that the historical test used **ten threads**. That recollection motivated this separate investigation of `experiments/multithread/og_hat.cpp`. The completed investigation retained that file's eight-worker branch, so it does not reproduce the clarified ten-thread configuration.

The archived surface is a **cosine bell**, `cos(x*3.141/2) * cos(y*3.141/2)`, on `[-1,1]²`, rather than a Gaussian. The original camera, light, triangle construction, per-pixel intersection loops and fixed eight-worker partition are retained. Only temporary copies are edited: the single/multithread switch, pixel width, mesh subdivision count, and dedicated timer instrumentation. Terminal display already defaults to false. Both tested pixel counts divide evenly among eight workers, avoiding the archive's remainder-handling defect for these particular runs.

## Why test two build modes?

The original build command used for the remembered timing is unknown. An unoptimized `-O0` build and optimized `-O2` build are therefore separate hypotheses, not reconstructions of a confirmed original compiler configuration. The original code copies nested vectors frequently; optimization can change both its absolute runtime and the relative cost of parallel execution.

All runs use Apple clang 21.0.0 with `-std=c++17 -pthread` on the same Apple M4 (4 performance cores and 6 efficiency cores), arm64, macOS 27.0.1. Eight workers are the original program's hard-coded value; automatic ten-worker selection from the maintained renderer is not substituted here.

## Workload selection

The unoptimized session uses 120×60 pixels, grid 12 (288 triangles). The optimized session uses 240×120 pixels, grid 24 (1,152 triangles), exceeding the archive's default 200×100 pixels, grid 10 (200 triangles). These settings were selected during the earlier investigation to keep single-worker trials around 20 seconds, then reused unchanged for this fresh computation-only comparison. They were not searched to obtain a target speedup.

The two build modes use **different workloads**. Compare one worker against eight within each session; the sessions are not a controlled measurement of the effect of optimization alone.

## Repeated results

![Original cosine-bell renderer timing in separate optimized and unoptimized workloads](images/bell-thread-scaling.png)

| Build and workload | One worker: median computation (range) | Eight workers: median computation (range) | Speedup |
| --- | ---: | ---: | ---: |
| `-O0`, 120×60, grid 12 | 19.3021 s (19.1802–19.4737) | 4.5679 s (4.5292–4.7575) | 4.23× |
| `-O2`, 240×120, grid 24 | 19.4267 s (18.9073–19.9344) | 10.7165 s (9.1563–11.0250) | 1.81× |

Every output matched across the two worker settings and all eight runs within each repeated session (two warmups plus six measured trials), and matched the earlier same-workload output. The larger optimized case showed substantial multithread runtime variation, visible in the chart's min–max bars. All values in this table use the dedicated rendering-computation timer, not whole-process time or the archive's original broader internal timer.

**These eight-worker measurements are a different configuration from the remembered ten-thread result.** They establish measurable improvements for the original bell code under the recorded conditions. The precise historical workload, compiler options and timing conditions remain unavailable. No ten-worker bell measurement was performed in this investigation, and the eight-worker results cannot establish its ten-worker speedup. No allocator changes, core-affinity changes or parameter search was used to pursue a preferred ratio.

![Newly generated cosine-bell output from the original renderer](images/bell-demo.png)

Newly generated during this investigation from the earlier `-O2` session at 240×120 pixels, grid 24 (1,152 triangles), with the original camera and light. The original floating-point text output was clamped to `[0,1]`, rounded to 8-bit grayscale, and converted from PGM to PNG. This preserves the archived rendering algorithm, including its documented limitations; it is not an original saved image.

## Method and reproduction

```sh
python3 scripts/benchmark_bell.py --width 120 --grid 12 --optimizations O0 --rounds 3 --output /tmp/my-bell-compute.json
python3 scripts/benchmark_bell.py --width 240 --grid 24 --optimizations O2 --rounds 3 --output /tmp/my-bell-compute.json
```

The runner requires Python's standard library and a C++ compiler. Start with a fresh output filename for an independent run. It compiles temporary copies and removes them afterward. Repeated sessions get one warmup per worker setting, followed by three measured rounds with the order reversed each round. Every process has a 60-second timeout. Results append as separately labeled sessions to the selected output JSON. The published [computation record](benchmarks/bell-compute.json) includes every trial, compiler/hardware metadata, UTC timestamps, source hashes, instrumented-build hashes, and output hashes.

A `std::chrono::steady_clock` timer is injected immediately before the single/multithread dispatch branch and stopped immediately after it, before any pixel data is written. Camera, mesh, normals, brightness preparation, and the pixel buffer already exist. The interval includes intersection/visibility computation, assigning pixel values, and worker launch/join. Startup, scene construction, file output, terminal display, and hashing are excluded. See the [precise timing boundaries](timing.md).

End-to-end wall time and the original internal timer are diagnostics only. The source's hard-coded estimated-time message is ignored. Pixel counts and printed image dimensions are checked, and all pixel-output hashes must match across worker counts within a workload. Hash equality establishes equal output, not geometric correctness: archived nearest-hit and shared-edge defects remain.

The [earlier record](benchmarks/bell-scaling.json), including its calibration, retains its broader timing scope and is not an input to the current chart. These are fresh runs: changes in the ratios also reflect variation between sessions, rather than an isolated measurement of the effect of excluding I/O.

Thermal state, power mode and other desktop activity are not controlled. These are small, sequential experiments on one machine, not a general scaling claim or a disproof of timings obtained on different hardware/builds.

The optional chart requires Matplotlib and the image conversion requires Pillow. Regenerate them from the recorded data and actual rendered PGM with:

```sh
python3 scripts/benchmark_bell.py --chart --output docs/benchmarks/bell-compute.json
python3 -c 'from PIL import Image; Image.open("/tmp/bell-demo.pgm").save("docs/images/bell-demo.png")'
```

Chart generation expects the two representative sessions in the recorded JSON. For independent reruns, use `--output /tmp/my-bell-results.json` to keep the publication measurement record unchanged.
