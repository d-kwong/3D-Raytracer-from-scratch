# Publication and maintenance notes

The original rendering project was hand-coded by Derek Kwong. Its mathematical reasoning, comments, surface experiments, and separate implementations are preserved in `experiments/`.

The maintained demonstration, regression tests, repository organization, and documentation were prepared with AI assistance during this publication effort. They are new maintenance work, not a reconstruction of the original project's development history. New generated figures are labeled separately from preserved original outputs.

## What was changed

The maintained C++ demonstration derives from `experiments/multithread/render.cpp`. It retains the vector-based geometry, grid triangulation, plane intersection and signed-edge tests, Rodrigues camera rotation, flat diffuse shading, and independent pixel workers.

Corrections include updating the nearest-hit distance, accepting shared boundaries with tolerance, rejecting nearly parallel rays and invalid normals, safe normalization and finite brightness, complete worker coverage, safe automatic worker selection, proper ASCII row endings, and checked output. The centroid calculation uses division by three; camera rotation uses accurate angle conversion. The original swirl's approximate constants remain explicit in the scene.

The root interface adds command-line controls, a C++17 Makefile, PGM output, a small reproducible demonstration, and regression tests. Historical variants have not all been repaired or executed.

## Preservation and exclusions

The Google Drive source was read and copied; it was not edited. No existing Git history was found. Commits in this repository record the actual publication work with current timestamps, rather than imitating the project's earlier development.

The publication copy omits compiled binaries, editor configuration, `.DS_Store`, intermediate frame sequences, and raw floating-point output dumps. The duplicate `test.mov` is excluded because its encoded media payload matches the retained `test.mp4`. Useful original images, the retained PDF, and two videos remain. Personal absolute file paths in source were replaced with relative paths, and `Triangles/render.py` creates its local frame-output directory. These changes apply only to the publication copy; historical rendering algorithms were not rewritten.

At the author's explicit request, a supplied personal photograph is included as a resized JPEG with metadata removed and the personal path visible in the photographed editor redacted. The author confirmed that it shows work on the earliest Python files on a plane and notebook concepts covering 3D rotation matrices, point-in-triangle testing, and line–plane intersection. The caption does not infer a date, route, or location or transcribe unreadable equations.

No open-source license was selected. Public availability does not itself grant an open-source license. The original author can choose terms later.
