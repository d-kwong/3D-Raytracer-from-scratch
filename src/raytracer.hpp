#ifndef RAYTRACER_HPP
#define RAYTRACER_HPP

// Derived from the original multithread/render.cpp. The explicit vector
// operations, plane intersection, edge tests, and Rodrigues rotation remain
// visible here so the geometry can be followed without a graphics library.
#include <algorithm>
#include <array>
#include <cmath>
#include <cstddef>
#include <functional>
#include <limits>
#include <stdexcept>
#include <thread>
#include <vector>

namespace raytracer {
using Vec = std::array<double, 3>;
using Face = std::array<Vec, 3>;
constexpr double epsilon = 1e-10;
constexpr double pi = 3.14159265358979323846;

inline double dot(const Vec& a, const Vec& b) {
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2];
}
inline Vec cross(const Vec& a, const Vec& b) {
    return {a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]};
}
inline Vec subtract_v(const Vec& a, const Vec& b) {
    return {a[0]-b[0], a[1]-b[1], a[2]-b[2]};
}
inline Vec add_v(const Vec& a, const Vec& b) {
    return {a[0]+b[0], a[1]+b[1], a[2]+b[2]};
}
inline Vec multiply_v(const Vec& v, double value) {
    return {v[0]*value, v[1]*value, v[2]*value};
}
inline Vec normalize(const Vec& v) {
    double norm = std::sqrt(dot(v,v));
    if (!std::isfinite(norm) || norm <= epsilon)
        throw std::invalid_argument("cannot normalize a zero, tiny, or non-finite vector");
    return multiply_v(v,1.0/norm);
}
inline Vec compute_normal(const Face& face) {
    return normalize(cross(subtract_v(face[1],face[0]),subtract_v(face[2],face[0])));
}

struct Intersection {
    bool hit = false;
    Vec point{};
    double t = 0;
};
// N and D are unit vectors. Reject parallel rays before dividing.
inline Intersection plane_intercept(const Face& face, const Vec& N, const Vec& P, const Vec& D) {
    double ND = dot(N,D);
    if (std::abs(ND) <= epsilon) return {};
    double t = dot(N,subtract_v(face[0],P))/ND;
    if (!std::isfinite(t) || t < 0) return {};
    return {true, add_v(P,multiply_v(D,t)), t};
}
inline bool check_inside(const Face& face, const Vec& N, const Vec& I) {
    double p1 = dot(N,cross(subtract_v(face[1],face[0]),subtract_v(I,face[0])));
    double p2 = dot(N,cross(subtract_v(face[2],face[1]),subtract_v(I,face[1])));
    double p3 = dot(N,cross(subtract_v(face[0],face[2]),subtract_v(I,face[2])));
    // Include shared edges/vertices; the original strict signs left cracks.
    return (p1 >= -epsilon && p2 >= -epsilon && p3 >= -epsilon) ||
           (p1 <= epsilon && p2 <= epsilon && p3 <= epsilon);
}
// Rodrigues' formula; callers supply a unit rotation axis k.
inline Vec rotate_point(const Vec& v, const Vec& k, double theta) {
    Vec term1 = multiply_v(v,std::cos(theta));
    Vec term2 = multiply_v(cross(k,v),std::sin(theta));
    Vec term3 = multiply_v(k,dot(k,v)*(1-std::cos(theta)));
    return add_v(add_v(term1,term2),term3);
}
inline double compute_brightness(const Vec& P, const Vec& N, const Vec& LP) {
    return std::clamp(dot(N,normalize(subtract_v(LP,P))),0.0,1.0);
}
inline std::vector<double> linspace(double a, double b, std::size_t n) {
    if (n < 2) throw std::invalid_argument("linspace requires at least two points");
    std::vector<double> result(n);
    for (std::size_t i=0; i<n; ++i) result[i]=a+(b-a)*i/(n-1);
    return result;
}
inline std::vector<Vec> create_pixels(std::size_t width, std::size_t height) {
    auto x = linspace(-2.25,2.25,width);
    auto z = linspace(1.125,-1.125,height);
    std::vector<Vec> pixels;
    pixels.reserve(width*height);
    for (double zi : z) for (double xi : x) {
        Vec P = rotate_point({xi,3.0,zi},{1,0,0},pi*30/180);
        pixels.push_back(rotate_point(P,{0,0,1},pi*45/180));
    }
    return pixels;
}
inline double z_func(double x, double y) {
    // Original swirl, including the author's approximations to pi and e.
    // Keeping them distinguishes this surface from a silently changed model.
    return 0.2*std::sin(3*3.141*std::sqrt(x*x+y*y)+3*std::atan2(y,x))*
           std::pow(2.714,-(x*x+y*y));
}
struct Triangle {
    Face face;
    Vec normal;
    double brightness;
};
inline Triangle make_triangle(const Face& face, const Vec& light) {
    Vec normal = compute_normal(face);
    Vec center = multiply_v(add_v(add_v(face[0],face[1]),face[2]),1.0/3.0);
    return {face,normal,compute_brightness(center,normal,light)};
}
inline std::vector<Triangle> make_scene(std::size_t grid) {
    if (grid < 1) throw std::invalid_argument("grid must be positive");
    auto x = linspace(-1.5,1.5,grid+1);
    auto y = linspace(-1.5,1.5,grid+1);
    const Vec light{2,2,2};
    std::vector<Triangle> triangles;
    triangles.reserve(2*grid*grid);
    for (std::size_t i=0; i<grid; ++i) for (std::size_t j=0; j<grid; ++j) {
        Vec a{x[j],y[i],z_func(x[j],y[i])};
        Vec b{x[j+1],y[i],z_func(x[j+1],y[i])};
        Vec c{x[j],y[i+1],z_func(x[j],y[i+1])};
        Vec d{x[j+1],y[i+1],z_func(x[j+1],y[i+1])};
        triangles.push_back(make_triangle({a,b,c},light));
        triangles.push_back(make_triangle({b,d,c},light));
    }
    return triangles;
}
inline void write_pixel_data(std::vector<double>& colors, const std::vector<Triangle>& triangles,
                             const Vec& D, const std::vector<Vec>& pixels,
                             std::size_t start, std::size_t end) {
    for (std::size_t i=start; i<end; ++i) {
        double min_t = std::numeric_limits<double>::infinity();
        double brightness = 0;
        for (const auto& triangle : triangles) {
            auto I = plane_intercept(triangle.face,triangle.normal,pixels[i],D);
            if (I.hit && I.t < min_t && check_inside(triangle.face,triangle.normal,I.point)) {
                min_t = I.t;
                brightness = triangle.brightness;
            }
        }
        colors[i] = brightness;
    }
}
inline std::size_t worker_count(std::size_t requested, std::size_t count, unsigned available) {
    if (!count) return 0;
    return std::min(count,requested ? requested : std::max(1u,available));
}
inline std::vector<double> render(const std::vector<Triangle>& triangles,
                                  const std::vector<Vec>& pixels, const Vec& D,
                                  std::size_t requested_threads) {
    std::vector<double> colors(pixels.size(),0);
    std::size_t count = worker_count(requested_threads,pixels.size(),std::thread::hardware_concurrency());
    if (count <= 1) {
        write_pixel_data(colors,triangles,D,pixels,0,pixels.size());
        return colors;
    }
    std::vector<std::thread> threads;
    threads.reserve(count);
    try {
        for (std::size_t i=0; i<count; ++i) {
            // Proportional endpoints cover remainders, with disjoint writes.
            threads.emplace_back(write_pixel_data,std::ref(colors),std::cref(triangles),
                                 std::cref(D),std::cref(pixels),pixels.size()*i/count,
                                 pixels.size()*(i+1)/count);
        }
    } catch (...) {
        for (auto& thread : threads) thread.join();
        throw;
    }
    for (auto& thread : threads) thread.join();
    return colors;
}
} // namespace raytracer
#endif
