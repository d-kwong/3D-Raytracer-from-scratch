# Verification record

This record separates the maintained demonstration from the preserved experiments. Only checks with recorded outcomes should be treated as completed.

## Maintained demonstration

`make test` passed with the maintained C++17 build and Python 3 integration tests. The C++ geometry suite also passed with AddressSanitizer and UndefinedBehaviorSanitizer. The suite covers nearest-hit order independence, parallel and behind-camera rays, shared edges and vertices, invalid normals, rotations, finite shading, zero reported hardware concurrency, workloads not divisible by worker count, more requested workers than pixels, CLI validation, PGM dimensions, and ASCII row widths. The normal build emitted no compiler warnings.

The 160×80 demonstration was executed with one worker and its PGM and PNG were visually inspected. Output bytes range from 0 to 254. Single-worker and six-worker outputs match exactly at 31×17 pixels with an 8×8 grid. These are correctness checks, not performance benchmarks.

Reproduction command for the new README image:

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
