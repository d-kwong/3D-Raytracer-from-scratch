#include "raytracer.hpp"
#include <chrono>
#include <fstream>
#include <iostream>
#include <string>

namespace {
std::size_t number(const std::string& value) {
    if (value.empty() || value.find_first_not_of("0123456789") != std::string::npos)
        throw std::invalid_argument("expected a non-negative integer: " + value);
    return std::stoull(value);
}
void usage() {
    std::cout << "Usage: raytracer [--width N] [--height N] [--grid N] [--threads N]\n"
                 "                 [--output PATH] [--ascii] [--help]\n"
                 "Defaults: 160x80, grid 20 (800 triangles), threads 0 (automatic), render.pgm\n"
                 "Width/height: 2..4096; grid: 1..256; threads: 0..256.\n"
                 "Camera extent stays 4.5x2.25; use a 2:1 resolution for square pixels.\n";
}
}
int main(int argc, char** argv) {
    try {
        std::size_t width=160, height=80, grid=20, threads=0;
        std::string path="render.pgm";
        bool ascii=false;
        for (int i=1; i<argc; ++i) {
            std::string flag=argv[i];
            if (flag=="--help") { usage(); return 0; }
            if (flag=="--ascii") { ascii=true; continue; }
            if (flag!="--width" && flag!="--height" && flag!="--grid" && flag!="--threads" && flag!="--output")
                throw std::invalid_argument("unknown option: " + flag);
            if (++i==argc) throw std::invalid_argument("missing value for " + flag);
            std::string value=argv[i];
            if (flag=="--output") { path=value; continue; }
            auto n=number(value);
            if (flag=="--width") width=n;
            else if (flag=="--height") height=n;
            else if (flag=="--grid") grid=n;
            else threads=n;
        }
        if (width<2 || width>4096 || height<2 || height>4096 || grid<1 || grid>256 || threads>256)
            throw std::invalid_argument("settings out of range; see --help");
        // Fail before rendering if the output cannot be opened.
        std::ofstream output(path,std::ios::binary);
        if (!output) throw std::runtime_error("cannot open output: " + path);
        auto start=std::chrono::steady_clock::now();
        auto pixels=raytracer::create_pixels(width,height);
        auto triangles=raytracer::make_scene(grid);
        auto D=raytracer::compute_normal({pixels[0],pixels[width],pixels[1]});
        auto colors=raytracer::render(triangles,pixels,D,threads);
        output << "P5\n" << width << ' ' << height << "\n255\n";
        for (double p : colors) output.put(static_cast<char>(std::lround(std::clamp(p,0.0,1.0)*255)));
        output.close();
        if (!output) throw std::runtime_error("failed writing output: " + path);
        if (ascii) {
            constexpr char ramp[]=" .:-=+*#%@";
            for (std::size_t i=0; i<colors.size(); ++i) {
                std::cout << ramp[static_cast<std::size_t>(std::clamp(colors[i],0.0,1.0)*9)];
                if ((i+1)%width==0) std::cout << '\n';
            }
        }
        double seconds=std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count();
        std::cerr << width << 'x' << height << ", " << triangles.size() << " triangles, "
                  << raytracer::worker_count(threads,pixels.size(),std::thread::hardware_concurrency())
                  << " workers; wrote " << path << " in " << seconds << " seconds\n";
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "raytracer: " << e.what() << '\n';
        return 1;
    }
}
