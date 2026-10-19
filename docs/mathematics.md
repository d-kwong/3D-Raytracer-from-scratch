# Rendering mathematics

These notes describe the maintained C++ demonstration. The historical files preserve earlier versions of the calculations, including mistakes; the equations here should not be read as a claim that every original variant implements them correctly.

## From a sampled surface to triangles

The swirl is a height field $z=f(x,y)$ on $[-1.5,1.5]^2$. The retained formula is

$$
f(x,y)=0.2\sin\left(3\pi_0\sqrt{x^2+y^2}+3\operatorname{atan2}(y,x)\right)e_0^{-(x^2+y^2)},
\qquad \pi_0=3.141,\quad e_0=2.714.
$$

The approximate constants are inherited scene choices, not an assertion that $e=2.714$. They remain to avoid silently changing the original surface. Camera angle conversion uses an accurate value of $\pi$.

The angular term has no unique continuous limit at the origin: the original formula uses `atan2(0,0)` at the sampled center. The maintained mesh retains that behavior, so changes in grid resolution can alter the central facets; this is not a smooth-surface convergence claim.

Each grid cell with corner points $A,B,C,D$ is split along one diagonal into two consistently wound triangles. A grid of $g\times g$ cells produces $2g^2$ faces. The displayed object is this piecewise-planar mesh, not the continuous function itself.

For triangle $A,B,C$, let $E_1=B-A$ and $E_2=C-A$. Then

$$
N=E_1\times E_2,\qquad \hat{n}=N/\lVert N\rVert.
$$

Vertex order determines the normal direction and therefore the lit side. A zero-area triangle cannot supply a valid normal. The maintained implementation rejects invalid geometry instead of dividing by zero and propagating nonfinite values.

## Orthographic rays and plane intersection

The unrotated camera is a rectangle at constant $y$, with columns sampled along $x$ and rows along $z$. Rotating this rectangle and its viewing direction moves the camera around the scene. Ray origins vary from pixel to pixel, while direction $D$ stays constant. This is orthographic projection: changing the plane's distance alone does not introduce perspective foreshortening.

A point on a ray is $I(t)=P+tD$. A point on the triangle's plane satisfies $\hat{n}\cdot(I-A)=0$. Substitution gives

$$
\hat{n}\cdot(P+tD-A)=0
\quad\Longrightarrow\quad
t=\frac{\hat{n}\cdot(A-P)}{\hat{n}\cdot D}.
$$

If $|\hat{n}\cdot D|$ is too small, the ray is parallel or nearly parallel to the plane and the division is unreliable. Such cases are rejected. Only forward intersections with $t\geq0$ are candidates. Since every face for a given ray uses the same direction, comparing $t$ values selects the closest hit even without converting to Euclidean distance.

The original pixel loop compared each hit with an initial distance limit but did not update that distance after accepting a hit. Later faces could overwrite nearer ones. The maintained loop updates the closest distance together with the brightness and starts at infinity instead of an arbitrary cutoff.

## Is the point inside?

For a candidate intersection $I$, compute signed edge expressions

$$
s_0=\hat{n}\cdot((B-A)\times(I-A)),
$$

$$
s_1=\hat{n}\cdot((C-B)\times(I-B)),\qquad
s_2=\hat{n}\cdot((A-C)\times(I-C)).
$$

For consistently ordered vertices, an interior point lies on the same side of every edge. Allowing a small tolerance around zero includes edges and vertices. The original strict sign test excluded zero, which could reject points exactly on shared mesh edges and leave cracks. This is a floating-point boundary policy, not an exact-predicate computational geometry implementation; extremely small, large, or ill-conditioned input geometry remains outside the demonstrated scene scale.

## Rotation

For unit axis $k$ and angle $\theta$, Rodrigues' formula rotates a vector $v$:

$$
v'=v\cos\theta+(k\times v)\sin\theta+k(k\cdot v)(1-\cos\theta).
$$

The camera applies an $x$-axis elevation rotation followed by a $z$-axis azimuth rotation. Order matters: rotations about different axes generally do not commute. Rotating the complete camera plane preserves its rectangular geometry; rotating its direction consistently preserves the orthographic ray arrangement.

## Flat lighting

For face centroid $G=(A+B+C)/3$ and light position $L$, define the unit light direction $\hat{\ell}=(L-G)/\lVert L-G\rVert$. The grayscale brightness is

$$
b=\max(0,\hat{n}\cdot\hat{\ell}).
$$

The maintained code uses exact division by three for the centroid, rejects a zero light-direction vector, and bounds finite output before conversion to grayscale. Lighting is constant over each triangle. A face pointing away from the light is dark, but no secondary ray tests whether another triangle blocks the light. A black pixel can therefore be either background or a valid unlit face.

## Work and numerical limits

With $W\times H$ pixels and $2g^2$ faces, the direct renderer performs $O(WHg^2)$ face tests. Workers split the pixel range without changing a pixel's face traversal. This makes single-worker versus multiple-worker equality a useful regression check, including workloads that do not divide evenly by the worker count.

There is no acceleration structure, antialiasing, shadow test, reflection model, or recursive path computation. Finite tolerances address the demonstrated geometry; they do not establish robustness for arbitrary imported meshes.
