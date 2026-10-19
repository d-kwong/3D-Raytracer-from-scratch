# What the speed comparisons time

The current speedup tables and charts use **elapsed rendering-computation time**. They exclude process startup, argument parsing, camera and mesh construction, normal/brightness precomputation, opening output files, image serialization, terminal printing, and output hashing.

They include the work required to execute the rendering phase: the pixel/triangle intersection loops, selecting visible faces, assigning pixel brightness, and creating, dispatching, and joining rendering workers. Thread-management cost belongs to the parallel rendering approach and is included rather than hidden. The maintained `render()` function also allocates its result buffer inside this interval; the archived programs initialize that buffer before their dispatch interval. Each speedup compares worker counts within the same implementation and workload, not the two implementations against each other.

## Timer boundaries

- **Maintained renderer:** a `std::chrono::steady_clock` timestamp immediately before `raytracer::render(...)` and another immediately after it returns. Pixels, triangles, lighting, and ray direction are already prepared; PGM and ASCII output follow the stop timestamp. The dedicated stderr line is `render computation: ... seconds`.
- **Archived bell and swirl:** the benchmark creates temporary source copies and injects steady-clock timestamps immediately before the existing single/multithread dispatch branch and immediately after it finishes, before the loop writing pixel data. The timer does not change the rendering calculations. The original archived files remain untouched.

These are wall-clock durations for the computation phase, which is the relevant quantity for how soon rendering finishes. Summing CPU time across workers would measure a different quantity; CPU-resource accounting is documented separately in [the utilization record](cpu-usage.md).

## Results and provenance

The benchmark scripts use only the explicit computation metric for medians, ranges, speedups, and chart bars. Process wall time and the older broad internal timer are retained as diagnostics in raw records. Chart generation rejects records without the computation metric, preventing old measurements from being relabeled as computation-only results.

Each configuration receives a warmup before measured rounds. Worker order is interleaved, and output hashes must match across worker settings. Full settings and individual trials are linked from the [maintained-renderer comparison](performance.md) and [bell investigation](bell-performance.md).

The earlier `thread-scaling.json`, `bell-scaling.json`, and `legacy-renderer.json` records remain as archival end-to-end measurements. Their old numbers are not used by the current computation-only charts. They were measured over a broader interval; no setup or I/O duration has been guessed and subtracted afterward. The current ratios come from fresh runs, so differences from the older values also include between-session variation.
