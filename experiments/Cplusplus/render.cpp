#include <iostream>
#include <vector>
#include <math.h>
#include <chrono>
#include <fstream>
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

double z_func(double x, double y){
    return cos(x*3.141/2)*cos(y*3.141/2);
}

double compute_brightness(vector<double> P, vector<double> N, vector<double> LP){
    return max(0.0,dot(N,normalize(subtract_v(LP,P))));
}

int main(){
    int n_pixels_w = 100;
    //processing time in seconds ~= n_pixels_w * n_pixels_h * n_faces^2 / 66,666.666
    int n_faces = 30;
    double camera_w = 3.0;
    double camera_h = 1.5;
    double camera_dist = 1.6;
    double camera_elev = 22.5;
    double camera_azim = 45;
    double camera_zshift = 0.2;
    double font_adjust = 1.0;//0.6
    int n_pixels_h = (int)(n_pixels_w*font_adjust/camera_w*camera_h);
    
    cout << "estimated processing time: "<<n_pixels_w * n_pixels_h * n_faces * n_faces / 66666.666 << " seconds" << endl;

    vector<double> light_pos = {-1,4,9};
    double brigthness_push = 0.0;

    vector<double> P(3);
    vector<double> temp_v;
    vector<vector<double>> temp;

    vector<double> c_x = linspace(-camera_w/2,camera_w/2,n_pixels_w);
    vector<double> c_z = linspace(camera_h/2+camera_zshift,-camera_h/2+camera_zshift,n_pixels_h);
    vector<vector<double>> pixels;
    
    for (int i = 0; i < n_pixels_h; i++){
        for (int j = 0; j < n_pixels_w; j++){
            P = {c_x[j],camera_dist,c_z[i]};
            P = rotate_point(P,{1,0,0},3.141*camera_elev/180);
            P = rotate_point(P,{0,0,1},3.141*camera_azim/180);
            pixels.push_back(P);
        }
    }

    vector<double> x = linspace(-1,1,n_faces+1);
    vector<double> y = linspace(-1,1,n_faces+1);
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
            brightnesses.push_back(compute_brightness(P,temp_v,light_pos));
            
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
            brightnesses.push_back(compute_brightness(P,temp_v,light_pos));
        }
    }
    auto t1 = chrono::high_resolution_clock::now();
    vector<double> D = compute_normal({pixels[0],pixels[n_pixels_w],pixels[1]});

    vector<vector<double>> intercepts;
    vector<double> I;
    vector<double> N;
    double min_t;
    double brightness;
    vector<char> c = {' ','.',':','-','=','+','*','#','%','@'};
    ofstream output("output.txt");
    for (int i = 0; i < n_pixels_w*n_pixels_h; i++){
        if (i%1000==0) cout << i << "/" << n_pixels_w*n_pixels_h<<endl; 
        if (i%n_pixels_w==0) output.flush();
	    min_t = 100;
        brightness = 0;
        for (int j = 0; j < n_faces*n_faces*2; j++){
            I = plane_intercept(faces[j],normals[j],pixels[i],D);
            if (I[0]){
                if (check_inside(faces[j],normals[j],{I[1],I[2],I[3]})&&I[4]>=0){
                    if (I[4]<min_t) brightness = brightnesses[j];
                }
            }
        }
        // cout<<c[(int)(brightness*10+brigthness_push)];
        // if (i%n_pixels_w==0){
        //    cout<<"\n";
        // }
        output << brightness << " ";
    }
    output.close();
    //cout << "\n";
    cout<<"image dimensions: "<<n_pixels_w<<"x"<<n_pixels_h<<endl;
    auto t2 = chrono::high_resolution_clock::now();
    chrono::duration<double> d2 = t2-t1;
    cout<<"processing time: "<<d2.count()<<" seconds"<<endl;

    return 0;
}
