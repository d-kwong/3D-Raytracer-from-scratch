# Guide to the preserved experiments

The `experiments/` tree is a publication copy of the original project. Original mathematical comments and separate variants are retained. Personal absolute file paths were made relative; generated executables, editor settings, raw pixel dumps, and intermediate video frames were excluded. The source folder itself was not modified.

These are historical experiments, not independently supported entry points. A successful syntax check does not establish that their images, visibility logic, dimensions, or runtime behavior are correct. Use the root demonstration for the verified reproduction path.

| Folder | What it contains |
| --- | --- |
| `Cplusplus/` | Direct C++ rendering variants and Python plotting helpers |
| `Triangles/` | Python geometry tests, camera placement, rendering and rotation examples; a retained PDF and videos |
| `Testing/` | Focal-point exploration and associated images |
| `multithread/` | C++ surface variants, worker experiments, terminal animation, and Python output helpers |
| `sdl_display/` | SDL window/display experiments |
| `images/` | Preserved original renderings, with unverified exact generation settings |

## Optional dependencies

The root C++ demonstration needs none of these packages. To inspect the Python examples in a separate environment:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install numpy matplotlib opencv-python
```

NumPy supplies array/vector operations, Matplotlib supplies plotting and image display, and OpenCV (`cv2`, distributed as `opencv-python`) is used to write PNG images. Dependencies are unpinned because an original tested environment was not recorded. Some scripts assume matching output dimensions or particular working directories; inspect their constants before running them. Relative paths in the publication copy do not guarantee that every historical pipeline is complete.

SDL examples additionally require SDL2 development headers and libraries. On systems with `sdl2-config`, a representative compile command is:

```sh
c++ -std=c++17 experiments/sdl_display/main.cpp $(sdl2-config --cflags --libs) -o /tmp/raytracer-sdl
```

This is an optional historical example, not part of `make` or the root test suite. Its graphical event loop requires a display session.

## Known limitations and interpretation

- Several C++ variants share the original nearest-hit bug: the current minimum distance is not updated when selecting a face. Their rendered brightness can depend on triangle traversal order.
- Strict edge-sign tests can reject shared edges and vertices. Exact equality checks for parallel rays and unchecked normalization do not address numerical degeneracies.
- Some threaded loops use integer division without assigning remainder pixels. They can also assume that `hardware_concurrency()` returns a nonzero count.
- Original ASCII row breaks and output handling have defects. Image helpers can assume hard-coded dimensions or preexisting floating-point dumps.
- `render_polar.cpp` and `render_sphere.cpp` are duplicate partial-sphere variants. Their naming does not establish full-sphere coverage.
- Embedded processing-time formulas and hardware comments are historical estimates, not reproducible benchmark results.

The maintained renderer corrects the relevant geometry, worker coverage, and I/O issues while keeping the original approach. The historical files remain useful for reading the calculations and comparing implementations; they are not golden references for the corrected output.

The files show exploration of surfaces, camera parameters, resolution, terminal output, images, animation, and threading. They do not by themselves establish which version came first, why each choice was made, or which trials the author considered successful. No such narrative has been inferred here.

The [preservation inventory](../experiments/README.md) gives more detailed file exclusions, source-path edits, dependency notes, and media inspection results.
