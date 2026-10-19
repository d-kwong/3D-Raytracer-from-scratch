# Verification record

This record separates the maintained demonstration from the preserved experiments. Only checks with recorded outcomes should be treated as completed.

## Maintained demonstration

`make test` passed with the maintained C++17 build and Python 3 integration tests. The C++ geometry suite also passed with AddressSanitizer and UndefinedBehaviorSanitizer. The suite covers nearest-hit order independence, parallel and behind-camera rays, shared edges and vertices, invalid normals, rotations, finite shading, zero reported hardware concurrency, workloads not divisible by worker count, more requested workers than pixels, CLI validation, PGM dimensions, and ASCII row widths. The normal build emitted no compiler warnings.

The 160×80 demonstration was executed with one worker and its PGM and PNG were visually inspected. Output bytes range from 0 to 254. Single-worker and six-worker outputs match exactly at 31×17 pixels with an 8×8 grid. These are correctness checks, not performance benchmarks.

Reproduction command for the small quick-start image (retained as `docs/images/swirl-demo.png`):

```sh
make
./build/raytracer --width 160 --height 80 --grid 20 --threads 1 --output render.pgm
make test
```

Scene settings: the original swirl height field over `[-1.5, 1.5]²`; 20×20 cells, 800 triangles; orthographic camera width 4.5, height 2.25, distance 3, elevation 30°, azimuth 45°; light `(2, 2, 2)`. The PGM output is converted to PNG for README display without rerendering the scene.

For the publication preview, Pillow was used only to convert the image:

```sh
python -m pip install Pillow  # optional figure preparation, not a renderer dependency
python -c 'from PIL import Image; Image.open("render.pgm").save("docs/images/swirl-demo.png")'
```

The PNG retains the native 160×80 pixels and is displayed larger in the README. The default PGM's SHA-256 in this environment was `d00f33ba11f1067598614aff5bcdb24407ea4345fdb0a85b52dd1529a9722b7c`. Floating-point and math-library differences can affect exact image bytes on other systems.

A clean temporary checkout built and passed the documented reproduction and complete test suite; its PGM matched the working-folder image byte for byte. All local Markdown links resolved, and GitHub's Markdown API recognized the display and inline equations. The final README and figures were also inspected visually. The original source's 77-file hash manifest showed no changes. The publication audit checked staged files and commit contents for credentials, personal paths, and unwanted generated files; the supplied photograph's visible personal path was redacted and its EXIF metadata removed.

## Historical experiments

All 12 historical C++ files and `banana.c` passed compiler syntax checks, and all 12 Python files parsed. A small original terminal example ran. These results establish basic executability, not rendering correctness or successful execution of every historical program.

The publication environment has NumPy and SDL2. Matplotlib and OpenCV are absent from the bundled Python environment, so graphical Python and video pipelines are not claimed as reproduced. Original images and the PDF were visually inspected. The two retained MPEG-4 videos passed container and metadata inspection. Sampled frames from `hat_15_40.mp4` show a changing grayscale hat. Sampled frames from `test.mp4` are uniformly dark green; this artifact is retained as an original test file, not a successful rendering result. Exact generation settings for the original media have not been verified.

Historical runtime estimates have not been validated as benchmarks. No expensive animation runs or large experiments are required for the maintained demonstration.

## README visuals

The higher-resolution cover and mesh comparison were generated in a later publication update. The cover is a fresh 1600×800 render with an 80×80 mesh (12,800 triangles), not an enlargement of the quick-start image. Camera, light, height function, and renderer are unchanged. The three mesh-comparison panels are fresh 480×240 renders with 8×8, 20×20, and 80×80 cells. The original-output gallery only fits the preserved images into labeled panels; it does not regenerate or reconstruct them.

```sh
make
python3 -m venv .venv
.venv/bin/python -m pip install Pillow
.venv/bin/python scripts/prepare_visuals.py
```

`prepare_visuals.py` runs the cover and comparison renders, then creates their PNGs and the original-output gallery. To recompose the figures without repeating existing renders, use `--reuse`. Pillow and the font used for panel labels are optional figure-preparation dependencies, not renderer dependencies. The published cover used 10 automatically selected workers; it took about 20 seconds in this session, which is an observation rather than a benchmark. To render just the cover's pixel data:

```sh
./build/raytracer --width 1600 --height 800 --grid 80 --threads 0 --output build/swirl-cover.pgm
```

The [banana recording](banana.md) captures actual output from the unmodified C program. The [performance record](performance.md) contains repeated timed renders and image-equivalence checks. These new figures and measurements are distinct from the recovered original outputs.

The update passed `make test`. The cover PNG was checked pixel-for-pixel against its PGM, and the looping banana GIF was checked for 63 frames with 100 ms per frame. Benchmark medians were independently recalculated from the raw samples, and image hashes matched within each measured workload. The preserved experiment sources have no changes; the original source folder still matches its 77-file hash manifest.

Following the author's clarification about the original bell-shaped scene, a separate investigation exercised the archived `og_hat.cpp` with one and eight workers. One calibration session and two repeated sessions produced 20 matching-output runs in total. Its smaller unoptimized workload measured 3.92× speedup; the larger optimized workload measured 2.28×. The author subsequently clarified that the remembered 6–7× result used ten threads; these completed eight-worker tests use a different configuration. Exact settings, bounds, output hashes, and the original internal timer are recorded in [the bell investigation](bell-performance.md).

A subsequent sustained-render check measured actual process CPU time and macOS `top` samples rather than inferring utilization from thread count. The renderer reached a sampled 929% CPU peak, while native Activity Monitor showed a fully busy machine chart (0% idle); the author independently confirmed the visible saturation. The [CPU utilization record](cpu-usage.md) documents settings, resource accounting, interval samples, and the distinction between process CPU and machine-wide load.
