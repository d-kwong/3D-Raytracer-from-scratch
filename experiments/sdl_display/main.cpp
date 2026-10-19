#include <iostream>
#include <vector>
#include <math.h>
#include <chrono>
#include <fstream>
#include <thread>
#include <SDL2/SDL.h>
using namespace std;

vector<double> linspace(double a, double b, int n){
    vector<double> result(n);
    double step = (b-a)/(n-1);
    for(int i = 0; i<n; i++){
        result[i] = a+step*i;
    }
    return result;
}

double dot(vector<double> a, vector<double> b){
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2];
}

vector<double> cross(vector<double> a, vector<double> b){
    return {
        a[1]*b[2]-a[2]*b[1],
        a[2]*b[0]-a[0]*b[2],
        a[0]*b[1]-a[1]*b[0]
    };
}

vector<double> subtract_v(vector<double> a, vector<double> b){
    return {a[0]-b[0],a[1]-b[1],a[2]-b[2]};
}

vector<double> add_v(vector<double> a, vector<double> b){
    return {a[0]+b[0],a[1]+b[1],a[2]+b[2]};
}

vector<double> multiply_v(vector<double> v, double value){
    return {v[0]*value,v[1]*value,v[2]*value};
}

vector<double> normalize (vector<double> v){
    double norm = sqrt(v[0]*v[0]+v[1]*v[1]+v[2]*v[2]);
    return {v[0]/norm,v[1]/norm,v[2]/norm};
}

vector<double> compute_normal(vector<vector<double>> face){
    vector<double> E1 = subtract_v(face[1],face[0]);
    vector<double> E2 = subtract_v(face[2],face[0]);
    return normalize(cross(E1,E2));
}

vector<double> plane_intercept(vector<vector<double>> face, vector<double> N, vector<double> P, vector<double> D){
    double ND = dot(N,D);
    if (ND == 0) return {0};
    double t = dot(N,subtract_v(face[0],P))/ND;
    vector<double> I = add_v(P,multiply_v(D,t));
    return {1, I[0], I[1], I[2], t};
}

bool check_inside(vector<vector<double>> face, vector<double> N, vector<double> I){
    double p1 = dot(N,cross(subtract_v(face[1],face[0]),subtract_v(I,face[0])));
    double p2 = dot(N,cross(subtract_v(face[2],face[1]),subtract_v(I,face[1])));
    double p3 = dot(N,cross(subtract_v(face[0],face[2]),subtract_v(I,face[2])));
    return (p1>0 && p2>0 && p3>0) || (p1<0 && p2<0 && p3<0);
}

vector<double> rotate_point(vector<double> v, vector<double> k, double theta){
    vector<double> term1 = multiply_v(v,cos(theta));
    vector<double> term2 = multiply_v(cross(k,v),sin(theta));
    vector<double> term3 = multiply_v(k,dot(k,v)*(1-cos(theta)));
    return add_v(add_v(term1,term2),term3);
}

double compute_brightness(vector<double> P, vector<double> N, vector<double> LP){
    return max(0.0,dot(N,normalize(subtract_v(LP,P))));
}

vector<vector<double>> create_pixels(int n_pixels_w, int n_pixels_h, double camera_w, double camera_h, double camera_dist, double camera_elev, double camera_azim, double camera_zshift){
    vector<vector<double>> pixels;
    vector<double> P;
    vector<double> c_x = linspace(-camera_w/2,camera_w/2,n_pixels_w);
    vector<double> c_z = linspace(camera_h/2+camera_zshift,-camera_h/2+camera_zshift,n_pixels_h);
    for (int i = 0; i < n_pixels_h; i++){
        for (int j = 0; j < n_pixels_w; j++){
            P = {c_x[j],camera_dist,c_z[i]};
            P = rotate_point(P,{1,0,0},3.141*camera_elev/180);
            P = rotate_point(P,{0,0,1},3.141*camera_azim/180);
            pixels.push_back(P);
        }
    }
    return pixels;
}

void write_pixel_data(vector<double>& pixel_colors, vector<vector<vector<double>>>& faces, vector<double>& brightnesses, vector<vector<double>>& normals, vector<double> D, vector<vector<double>>& pixels, size_t start, size_t end){
    for (int i = start; i < end; i++){
        double min_t = 100;
        double brightness = 0;
        vector<double> I;
        for (int j = 0; j < faces.size(); j++){
            I = plane_intercept(faces[j],normals[j],pixels[i],D);
            if (I[0]){
                if (check_inside(faces[j],normals[j],{I[1],I[2],I[3]})&&I[4]>=0){
                    if (I[4]<min_t) brightness = brightnesses[j];
                }
            }
        }
        pixel_colors[i] = brightness;
    }
}

double z_func(double x, double y){
    return sin(3*3.141*sqrt(x*x+y*y)+3*atan2(y,x))*pow(2.714,-(x*x+y*y));
    //return fabs(sin(3*3.141*sqrt(x*x+y*y)+3*atan2(y,x))*pow(2.714,-(x*x+y*y)));
}


int main(){
    bool multithread = true;
    int n_threads = thread::hardware_concurrency(); // 8 usable cores on m2 macbook air. thread::hardware_concurrency() = number of available cores

    int n_pixels_w, n_faces, n_pixels_h;
    double camera_w, camera_h, camera_dist, camera_elev, camera_azim, camera_zshift, font_adjust;
    
    n_faces = 1;
    vector<double> x_domain = {-1.5,1.5};
    vector<double> y_domain = {-1.5,1.5};

    n_pixels_w = 200;
    camera_w = 4.5;
    camera_h = 4.5;
    camera_dist = 3.0;
    camera_elev = 30;
    camera_azim = 45;
    camera_zshift = 0.0;
    font_adjust = 1.0;
    n_pixels_h = (int)(n_pixels_w*font_adjust/camera_w*camera_h);
    
    vector<double> light_pos = {2,2,2};
    double brigthness_push = 0.0;

    vector<double> P;
    vector<double> temp_v;
    vector<vector<double>> temp;

    vector<vector<double>> pixels;
    pixels = create_pixels(n_pixels_w, n_pixels_h, camera_w, camera_h, camera_dist, camera_elev, camera_azim, camera_zshift);

    vector<double> x = linspace(x_domain[0],x_domain[1],n_faces+1);
    vector<double> y = linspace(y_domain[0],y_domain[1],n_faces+1);
    vector<vector<vector<double>>> faces;
    vector<vector<double>> normals;
    vector<double> brightnesses;

    for (int i = 0; i < n_faces; i++){
        for (int j = 0; j < n_faces; j++){
            temp.clear();
            P = {x[j],y[i],z_func(x[j],y[i])};
            temp.push_back(P);
            P = {x[j+1],y[i],z_func(x[j+1],y[i])};
            temp.push_back(P);
            P = {x[j],y[i+1],z_func(x[j],y[i+1])};
            temp.push_back(P);

            temp_v = compute_normal(temp);

            faces.push_back(temp);
            normals.push_back(temp_v);
            brightnesses.push_back(compute_brightness(multiply_v(add_v(add_v(temp[0],temp[1]),temp[2]),0.333333),temp_v,light_pos));
            
            temp.clear();
            P = {x[j+1],y[i],z_func(x[j+1],y[i])};
            temp.push_back(P);
            P = {x[j+1],y[i+1],z_func(x[j+1],y[i+1])};
            temp.push_back(P);
            P = {x[j],y[i+1],z_func(x[j],y[i+1])};
            temp.push_back(P);

            temp_v = compute_normal(temp);

            faces.push_back(temp);
            normals.push_back(temp_v);
            brightnesses.push_back(compute_brightness(multiply_v(add_v(add_v(temp[0],temp[1]),temp[2]),0.333333),temp_v,light_pos));
        }
    }

    cout << "using " << (multithread?"multithreaded":"single-thread") << " processing" << endl;
    cout << "estimated processing time: "<<n_pixels_w * n_pixels_h * n_faces * n_faces / (multithread?313555.234:66666.667) << " seconds" << endl;
    // estimated processing time based on m2 macbook air w/ 8 cores (4P 4E)
    // m4 macbook air is about 20% less time :) w/ 10 cores (4P 6E)
    auto t1 = chrono::high_resolution_clock::now();
    vector<double> D = compute_normal({pixels[0],pixels[n_pixels_w],pixels[1]});

    vector<char> c = {' ','.',':','-','=','+','*','#','%','@'};
    vector<double> pixel_colors(n_pixels_w*n_pixels_h,0);

    if (multithread){
        vector<thread> threads;
        int task_size = pixels.size()/n_threads;
        for (int i = 0; i < n_threads; i++){
            threads.emplace_back(write_pixel_data,ref(pixel_colors),ref(faces),ref(brightnesses),ref(normals),ref(D),ref(pixels),i*task_size,(i+1)*task_size);
        }
        for (auto& th:threads) th.join();
    } else {
        write_pixel_data(ref(pixel_colors),ref(faces),ref(brightnesses),ref(normals),ref(D),ref(pixels),0,pixels.size());
    }
    
    auto t2 = chrono::high_resolution_clock::now();
    chrono::duration<double> d2 = t2-t1;
    cout<<"processing time: "<<d2.count()<<" seconds"<<endl;
    cout<<"image dimensions: "<<n_pixels_w<<"x"<<n_pixels_h<<endl;

    int display_scale = 8;

    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        std::cerr << "SDL init failed: " << SDL_GetError() << "\n";
        return 1;
    }

    
    SDL_Window* window = SDL_CreateWindow(
        "RGB Image Viewer",
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
        n_pixels_w*display_scale, n_pixels_h*display_scale,
        SDL_WINDOW_SHOWN
    );

    SDL_Renderer* renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED);
    SDL_Texture* texture = SDL_CreateTexture(
        renderer,
        SDL_PIXELFORMAT_RGB24,
        SDL_TEXTUREACCESS_STREAMING,
        n_pixels_w*display_scale, n_pixels_h*display_scale
    );
    bool running = 1;
    SDL_Event event;
    std::vector<Uint8> sdl_pixels(n_pixels_w * n_pixels_h * 3 * display_scale * display_scale, 0);
    while (running) {
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_QUIT) running = false;
            if (event.type == SDL_KEYDOWN) {
                if (event.key.keysym.sym == SDLK_w) {camera_elev+=5;}
                if (event.key.keysym.sym == SDLK_s) {camera_elev-=5;}
                if (event.key.keysym.sym == SDLK_a) {camera_azim+=5;}
                if (event.key.keysym.sym == SDLK_d) {camera_azim-=5;}
                cout << "a key was pressed\n";


                pixels = create_pixels(n_pixels_w, n_pixels_h, camera_w, camera_h, camera_dist, camera_elev, camera_azim, camera_zshift);
                D = compute_normal({pixels[0], pixels[n_pixels_w], pixels[1]});
                t1 = chrono::high_resolution_clock::now();
                if (multithread){
                    vector<thread> threads;
                    int task_size = pixels.size()/n_threads;
                    for (int i = 0; i < n_threads; i++){
                        threads.emplace_back(write_pixel_data,ref(pixel_colors),ref(faces),ref(brightnesses),ref(normals),ref(D),ref(pixels),i*task_size,(i+1)*task_size);
                    }
                    for (auto& th:threads) th.join();
                } else {
                    write_pixel_data(ref(pixel_colors),ref(faces),ref(brightnesses),ref(normals),ref(D),ref(pixels),0,pixels.size());
                }
                t2 = chrono::high_resolution_clock::now();
                chrono::duration<double> d2 = t2-t1;
                cout<<"processing time: "<<d2.count()<<" seconds"<<endl;
            }
        }

        for (int i = 0; i < pixel_colors.size(); i++) {
            Uint8 value = (Uint8)(pixel_colors[i] * 255);
            for (int a = 0; a < display_scale; a++){
                for (int b = 0; b < display_scale*3; b++){
                    sdl_pixels[i/n_pixels_w*display_scale*n_pixels_w*display_scale*3+a*n_pixels_w*display_scale*3+(i%n_pixels_w)*display_scale*3+b] = value;
                }
            }
        }



        SDL_UpdateTexture(texture, nullptr, sdl_pixels.data(), n_pixels_w * 3 * display_scale);
        SDL_RenderClear(renderer);
        SDL_RenderCopy(renderer, texture, nullptr, nullptr);
        SDL_RenderPresent(renderer);
    }

    SDL_DestroyTexture(texture);
    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();    
    
    return 0;
}
