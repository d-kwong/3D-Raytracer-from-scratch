#include "../src/raytracer.hpp"
#include <iostream>
#include <string>

using namespace raytracer;
void require(bool value, const std::string& message) {
    if (!value) throw std::runtime_error(message);
}
bool close(double a, double b) { return std::abs(a-b)<1e-9; }

int main() {
    try {
        const Face face{{{0,0,0},{1,0,0},{0,1,0}}};
        const Vec normal=compute_normal(face), down{0,0,-1};
        auto hit=plane_intercept(face,normal,{0.2,0.2,2},down);
        require(hit.hit && close(hit.t,2) && close(hit.point[2],0),"line-plane intersection");
        require(!plane_intercept(face,normal,{0,0,1},{1,0,0}).hit,"parallel ray rejected");
        require(!plane_intercept(face,normal,{0,0,1},normalize({1,0,1e-12})).hit,"nearly parallel ray rejected");
        require(!plane_intercept(face,normal,{0,0,1},{0,0,1}).hit,"behind-camera hit rejected");
        require(check_inside(face,normal,{0.2,0.2,0}),"interior point");
        require(!check_inside(face,normal,{0.8,0.8,0}),"exterior point");
        require(check_inside(face,normal,{0.5,0.5,0}),"edge included");
        require(check_inside(face,normal,{0,0,0}),"vertex included");
        Face reversed{face[2],face[1],face[0]};
        require(check_inside(reversed,compute_normal(reversed),{0.2,0.2,0}),"reverse winding");
        bool invalid=false;
        try { compute_normal({Vec{0,0,0},Vec{0,0,0},Vec{1,0,0}}); }
        catch (const std::invalid_argument&) { invalid=true; }
        require(invalid,"degenerate normal rejected");
        invalid=false;
        try { normalize({std::numeric_limits<double>::infinity(),0,0}); }
        catch (const std::invalid_argument&) { invalid=true; }
        require(invalid,"non-finite vector rejected");
        Vec rotated=rotate_point({1,0,0},{0,0,1},pi/2);
        require(close(rotated[0],0) && close(rotated[1],1),"known quarter turn");
        Vec v{1,2,3}; rotated=rotate_point(v,normalize({1,1,0}),0.7);
        require(close(dot(v,v),dot(rotated,rotated)),"rotation preserves length");
        require(close(compute_brightness({0,0,0},normal,{0,0,1}),1),"front diffuse light");
        require(close(compute_brightness({0,0,0},normal,{0,0,-1}),0),"back diffuse light");

        Triangle near{face,normal,0.25};
        Face far_face=face;
        for (auto& point : far_face) point[2]=-2;
        Triangle far{far_face,normal,0.9};
        const std::vector<Vec> sample{{0.2,0.2,1}};
        require(render({near,far},sample,down,1)==std::vector<double>{0.25},"nearest hit replaces minimum");
        require(render({far,near},sample,down,1)==std::vector<double>{0.25},"nearest hit independent of storage order");
        Face adjacent{{{1,0,0},{1,1,0},{0,1,0}}};
        require(render({near,{adjacent,normal,0.25}},{{0.5,0.5,1}},down,1)[0]==0.25,"shared diagonal stays lit");

        Face large{{{-10,-10,0},{10,-10,0},{0,10,0}}};
        std::vector<Vec> pixels(35,{0,0,1});
        std::vector<Triangle> scene{{large,normal,0.7}};
        auto single=render(scene,pixels,down,1);
        require(single==std::vector<double>(35,0.7),"all known pixels lit");
        require(single==render(scene,pixels,down,6),"non-divisible thread partition");
        require(single==render(scene,pixels,down,100),"more workers than pixels");
        require(worker_count(0,35,0)==1,"zero hardware concurrency fallback");
        require(render(scene,{},down,0).empty(),"empty pixel buffer");

        pixels=create_pixels(31,17);
        auto triangles=make_scene(8);
        auto D=compute_normal({pixels[0],pixels[31],pixels[1]});
        auto colors=render(triangles,pixels,D,1);
        require(colors==render(triangles,pixels,D,6),"scene thread equivalence");
        require(std::any_of(colors.begin(),colors.end(),[](double c){return c>0;}),"scene has lit pixels");
        for (double c : colors) require(std::isfinite(c) && c>=0 && c<=1,"finite brightness in range");
        std::cout << "Geometry, visibility, rotation, shading, and thread regressions passed\n";
    } catch (const std::exception& e) {
        std::cerr << "FAIL: " << e.what() << '\n';
        return 1;
    }
}
