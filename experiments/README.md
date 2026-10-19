# Original experiments

These files preserve the separate rendering and geometry experiments found in the original project. Their algorithms and mathematical comments are retained, including known mistakes. The maintained, tested demonstration is described in the repository's main README.

| Folder/file | Contents |
| --- | --- |
| `Triangles/` | Python triangle intersection, camera, normal, rotation, sorting, and cosine-hat rendering experiments; an original PDF and two short videos |
| `Testing/` | Camera/focal-position exploration and seven original images |
| `Cplusplus/` | Earlier C++ renderers and Python plot/image helpers |
| `multithread/` | Swirl, hat, polar/sphere, banana, terminal animation, and worker-thread variants |
| `sdl_display/` | SDL2 display and interactive camera experiments; W/S changes elevation and A/D changes azimuth in `main.cpp` |
| `banana.c` | Standalone ASCII banana animation; runs until interrupted |
| `images/` | Original hat, sphere-like, and swirl outputs |

## Dependencies and optional use

The C++ files use the standard library except for `sdl_display/`, which requires SDL2. Python scripts require NumPy and generally Matplotlib; `Cplusplus/test.py` and `multithread/write_image.py` additionally require OpenCV (`opencv-python`). A separate environment avoids changing the maintained C++ setup:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install numpy matplotlib opencv-python
python experiments/Cplusplus/plot_3d.py
```

That plotting script opens an interactive window. Installing the optional packages was not part of publication verification. The original Python renderers can be slow: inspect their pixel, mesh, and frame counts before running them.

A historical C++ renderer can be compiled and run from its own directory:

```sh
cd experiments/multithread
c++ -std=c++17 -O2 -pthread render.cpp -o /tmp/original-raytracer
/tmp/original-raytracer
```

It prints terminal art and writes `output.txt` in the working directory. That command runs the historical algorithm, with the limitations below. It is not the corrected demonstration. For an SDL2 installation with `sdl2-config` available:

```sh
c++ -std=c++17 -O2 -pthread experiments/sdl_display/main.cpp \
  $(sdl2-config --cflags --libs) -o /tmp/original-sdl-raytracer
/tmp/original-sdl-raytracer
```

The Python pixel-dump helpers retain their original shape assumptions. `Cplusplus/test.py` expects a 2:1 image; `multithread/write_image.py` expects a square image. These assumptions do not match every C++ variant's default settings. Read the renderer's printed dimensions and adjust a copy of the helper before using it; the maintained demonstration writes its dimensions into the PGM header directly.

## Known limitations retained

- Several C++ ray loops test `t < min_t` without updating `min_t`; overlapping triangles can therefore be chosen by iteration order rather than distance.
- Strict edge comparisons exclude points exactly on triangle edges or vertices. Exact `N·D == 0` checks are fragile near parallel rays. Normalization lacks a guard for zero-length vectors.
- Some Python renderers pass a missing plane intersection to their inside-triangle test, and their sorted intersections can include negative distances. They are exploratory versions, not validated reference implementations.
- Thread partitions can omit a remainder, and automatic worker counts do not handle a reported count of zero. Some terminal output inserts the first newline after the first pixel.
- Polar/sphere variants use limited parameter ranges and can contain degenerate triangles. The filename alone does not establish complete spherical coverage.
- Timing estimates and Mac hardware comments are preserved historical notes, not a reproducible benchmark or a verified hardware comparison.
- Animation and SDL programs use fixed settings and may run until interrupted. Output handling and SDL error handling are limited.

## Original media and preservation record

All PNGs and `Triangles/hat.pdf` are original outputs, visually inspected during publication. Their exact generating commands and settings were not reconstructed, so the filenames are evidence of experiments rather than guaranteed reproduction recipes. `images/swirl.png` includes visible rendering artifacts; it is retained as an original result, not a correctness baseline.

`Triangles/videos/test.mp4` and `hat_15_40.mp4` are original MPEG-4 video files. Container inspection reports approximately 1.5 and 2 seconds respectively. Representative frames were decoded with AVFoundation and visually inspected at 0, 0.25, 0.5, 0.75, 1, and 1.4 seconds during publication. `hat_15_40.mp4` shows the pixelated cosine-hat surface from changing viewpoints. Every inspected `test.mp4` frame decoded as solid dark green, so that clip is retained as an original test artifact, not a successful rendering result. Exact generation settings and the cause of the green frames were not established. `test.mov` was excluded because its encoded media payload is byte-for-byte identical to `test.mp4`.

The publication copy excludes compiled executables (`main`, `app`, `single_thread_vid`, `multithread_vid`, `terminal_video`), `.vscode/`, `.DS_Store`, the raw `Cplusplus/output.txt` dump, and `Triangles/video_frames/`. Source files were copied without changing their algorithms. Personal absolute output paths were replaced with `output.txt` in C++ and paths relative to `__file__` in Python. `Triangles/render.py` now creates its local `video_frames/` output directory. The Google Drive source was left untouched.

Retained PNG metadata contains only image/Matplotlib information; the PDF records Matplotlib and its original creation timestamp; the videos identify the Lavf encoder. No private paths, contact details, location tags, or third-party datasets were found in retained media metadata. No vendored libraries or explicit external code attributions were found in these source files. The author has since identified Andy Sloane’s `donut.c` as the inspiration for `banana.c`; the [banana notes](../docs/banana.md) credit and link that work. This inspection is not an independent provenance determination.

During publication, all 12 C++ files and `banana.c` passed compiler syntax checks, and all 12 Python files parsed. The optional Python rendering, animation, and SDL display workflows were not executed end to end. Passing a syntax check does not establish numerical correctness.
