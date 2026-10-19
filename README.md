# 3D Raytracer (from scratch)

I built this project to understand the geometry behind turning a 3D surface into an image. I wrote the original Python, C++, and C programs by hand, including the vector operations, triangle intersections, camera rotations, lighting calculations, and threading experiments. I wanted to understand the mathematics by implementing it myself.

I’m sharing those original experiments alongside a small, corrected C++17 demonstration. The renderer traces one ray per pixel through a triangle mesh and shades the nearest triangle with a single light. My original implementations and mathematical comments are preserved in `experiments/`; the runnable demonstration includes later correctness and portability fixes.

<img src="docs/images/swirl-cover.png" alt="High-resolution swirl surface rendered by the maintained demonstration" width="960">

*New render from the maintained demonstration: 1600×800 pixels, 80×80 mesh cells (12,800 triangles). The small quick start below uses the same surface and camera; [figure reproduction commands](docs/verification.md#readme-visuals) include this larger render.*

## Run it

You need a C++17 compiler, `make`, and standard C++ threading support. There are no additional library dependencies for the demonstration. Python 3 is needed only for the integration tests in `make test`.

```sh
git clone https://github.com/d-kwong/3D-Raytracer-from-scratch.git
cd 3D-Raytracer-from-scratch
make
./build/raytracer --width 160 --height 80 --grid 20 --threads 1 --output render.pgm
make test
```

Open `render.pgm` in an image viewer that supports PGM. The file is a binary grayscale image, not the floating-point text format used by some original scripts. The README preview is a PNG conversion of this output.

```sh
# Use automatic worker selection and also print the image in the terminal.
./build/raytracer --ascii

# A denser mesh and larger image; this performs substantially more work.
./build/raytracer --width 320 --height 160 --grid 30 --output larger.pgm
```

| Option | Default | Meaning |
| --- | --- | --- |
| `--width` | `160` | Image width in pixels |
| `--height` | `80` | Image height in pixels |
| `--grid` | `20` | Mesh cells along each surface axis; two triangles per cell |
| `--threads` | `0` | Worker count; `0` selects automatically |
| `--output` | `render.pgm` | Destination PGM file |
| `--ascii` | Off | Also display grayscale characters in the terminal |

Run `./build/raytracer --help` for the allowed ranges. Large resolutions and meshes remain expensive even within these ranges.

The camera spans 4.5×2.25 world units, starts at distance 3, and rotates by 30° elevation and 45° azimuth. The light is at `(2, 2, 2)`. These are fixed scene settings in the code. The camera's world-space aspect ratio stays fixed when image dimensions change, so a different pixel aspect ratio stretches the image.

## The geometry

I represented each surface by sampling it on a grid and splitting every cell into two triangles. I computed a face normal from the cross product of its edges. For a triangle with vertices $A,B,C$, the unit normal is

$$
\hat{n}=\frac{(B-A)\times(C-A)}{\lVert(B-A)\times(C-A)\rVert}.
$$

In my orthographic renderers, I placed each pixel at an origin $P$ on a camera plane and gave all rays the same direction $D$. Substituting the ray $I=P+tD$ into the triangle's plane equation gives

$$
t=\frac{\hat{n}\cdot(A-P)}{\hat{n}\cdot D}.
$$

A valid hit needs a nonparallel ray, $t\geq0$, and an intersection inside the triangle. I checked triangle membership using the sign of the cross product along each edge, projected onto the normal. The intended visibility rule is to select the nearest valid $t$; the maintained version fixes a missing minimum-distance update in my original C++ loop.

I used a dot product between the face normal and the direction toward the light to shade each triangle. In the threaded C++ version, I evaluated brightness at the triangle centroid $G=(A+B+C)/3$:

$$
b=\max\left(0,\hat{n}\cdot\frac{L-G}{\lVert L-G\rVert}\right).
$$

This gives flat diffuse shading: brightness depends on how the face points toward the light. There are no shadows, reflections, recursive light transport, distance attenuation, or smooth interpolated normals.

I rotated the camera plane using Rodrigues' rotation formula. The [mathematical notes](docs/mathematics.md) derive the intersection, edge tests, rotation, and numerical safeguards in more detail.

![Early Python development with a notebook on an airplane](docs/images/early-python-on-a-plane.jpg)

*Working on the earliest Python files on a plane. My notebook covered 3D rotation matrices, the point-in-triangle check, and line–plane intersection—the geometry behind these experiments.*

## Where the mathematics lives

| Idea | Maintained implementation |
| --- | --- |
| Dot products, cross products, normalization | `src/raytracer.hpp`: vector helpers |
| Triangle normals, mesh construction, face brightness | `make_scene` and its geometry helpers |
| Ray–plane intersection | `plane_intercept` |
| Triangle boundaries | `check_inside` |
| Rodrigues rotation and camera plane | `rotate_point`, `create_pixels` |
| Nearest visible face and pixel work | `write_pixel_data`, `render` |
| Options and PGM output | `src/main.cpp` |

My threaded C++ renderer is preserved in [`experiments/multithread/render.cpp`](experiments/multithread/render.cpp). I wrote the plane-intersection and edge-test calculations directly, and split independent pixel work between worker threads. The maintained demonstration keeps that approach. Every pixel still checks every triangle, so the cost grows with **pixels × triangles**; increasing both image dimensions and both mesh dimensions multiplies the work quickly.

## Experiments and results

![Three preserved original outputs: a cosine hat, sphere-like surface, and swirl](docs/images/original-gallery.png)

*Recovered images from the original project, assembled into a gallery for this README. Their exact mesh, camera, and image-generation settings have not been verified; they are not correctness references for the maintained demonstration. The [original files](experiments/images/) are preserved separately.*

I wrote Python experiments to inspect triangles, normals, rotation, and camera placement. I also wrote C++ surface renderers, multithreading experiments, rotating and terminal animations, and an SDL display experiment. The preserved files are snapshots of that work; their filenames alone do not establish the order of every experiment.

The swirl function and its original approximate constants remain in the maintained scene. The historical variants also contain different surfaces and partial-sphere parameterizations. Names such as `render_sphere.cpp` should not be read as proof that they render a complete sphere. See the [experiment guide](docs/experiments.md) for dependencies and known issues.

The maintained version corrects nearest-hit selection, shared-edge rejection, numerical degeneracies, thread coverage, and output handling. Its images can therefore differ from the originals. Historical source is retained separately so that these changes do not erase the original reasoning. Original processing-time estimates are not presented as measured benchmarks.

The calculations connect vector geometry directly to visibility and shading. Details such as boundary inclusion and updating the nearest distance affect the resulting image as much as the surface equation does.

![The same swirl rendered with 128, 800, and 12800 triangles](docs/images/mesh-comparison.png)

*New comparison: each panel has 480×240 pixels and the same camera and light. Increasing the mesh density resolves the swirl while keeping its flat triangular shading visible. The angular surface formula has no unique continuous limit at the origin, so the changing center is a limitation of the original function, not proof of convergence to a smooth surface.*

## Single thread versus multiple threads

I added multithreading by splitting the pixels between CPU threads. In my original testing of the bell-shaped surface, ten threads gave roughly a **6–7× speedup** at relatively high image resolution and triangle counts. I also remember Activity Monitor’s CPU chart becoming fully saturated during those runs.

![Single-thread and eight-thread timing of the original cosine-bell renderer](docs/images/bell-thread-scaling.png)

*New recheck of the preserved bell renderer's eight-worker branch: 3.92× with an unoptimized build and 2.28× with an optimized build on this Apple M4. The panels use different workloads; compare worker counts within each panel. Every output matched its single-thread counterpart. This eight-worker configuration differs from the ten-thread historical test; the original build and exact workload remain unknown. The [bell investigation](docs/bell-performance.md) records the settings, raw trials, and a newly rendered bell image.*

The following separate worker-count sweep uses the maintained renderer on the same Apple M4, with four performance cores and six efficiency cores:

![Measured rendering time versus worker count for two image sizes](docs/images/thread-scaling.png)

| Render | One worker | Ten workers (automatic) | Speedup |
| --- | ---: | ---: | ---: |
| 160×80 pixels, 800 triangles | 54.0 ms | 16.8 ms | 3.22× |
| 640×320 pixels, 3,200 triangles | 3.168 s | 0.882 s | 3.59× |

These are medians of five timed runs per configuration after a warmup, with worker counts interleaved in shuffled order. Timings include process startup, scene construction, rendering, and writing the image. Every output hash matched across worker counts. This measures one machine and one session; it does not establish the old hardware estimates or guarantee the same speedup elsewhere.

The [performance notes and raw measurements](docs/performance.md) include another test of the original swirl renderer and explain why the unused result in the original array-summing `threading.cpp` makes that small test unreliable as an optimized benchmark.

A sustained 10-worker render was also checked in Activity Monitor during this publication update. The machine reached **0% idle**, and the renderer peaked at **929% sampled CPU usage**. Actual CPU use was measured separately from the worker count; see the [CPU utilization record](docs/cpu-usage.md) for the command and samples.

## Verification and next steps

The regression suite exercises intersections, visibility order, boundary hits, rotation, finite shading, and complete rendering across worker counts. The [verification record](docs/verification.md) distinguishes executed checks from historical examples that were only syntax-checked.

Useful extensions would be perspective projection, a spatial acceleration structure, smoother normals, and a clearer interface for selecting scenes. These are future work. The current demonstration deliberately keeps the geometry small enough to follow directly.

No license has been selected for this repository.

## One more recovered artifact: `banana.c`

I took inspiration from Andy Sloane’s famous [`donut.c`](https://www.a1k0n.net/2011/07/20/donut-math.html) and wrote my own rotating ASCII banana in C. I also arranged the source itself into a banana shape. This is a separate parametric rendering experiment from the triangle raycaster above.

![Rotating ASCII banana captured from the original C program](docs/images/banana-terminal.gif)

*New recording of the unchanged [original program](experiments/banana.c): 63 frames, one full turn. The program prints scrolling blocks; this GIF places those actual character blocks in a fixed viewport with a terminal-style background and yellow text.*

```sh
mkdir -p build
cc -O2 -std=gnu11 experiments/banana.c -lm -o build/banana
./build/banana
# Press Ctrl-C to stop.
```

The [capture notes and script](docs/banana.md) explain how to reproduce the GIF without reimplementing its geometry.
