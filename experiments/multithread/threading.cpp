#include <iostream>
#include <chrono>
#include <thread>
#include <vector>

using namespace std;

void product_range(int& target, vector<int>& nums, size_t start, size_t end){
    for (int i = start; i < end; i++){
        target += nums[i];
    }
}

int main(){
    
    vector<int> x;

    for (int i=1;i<8000001;i++) x.push_back(1);

    int answer = 0;

    vector<thread> threads;
    vector<int> partials(8,0);
    auto t1 = chrono::high_resolution_clock::now();
    for (int i = 0; i < 8; i++){
        threads.emplace_back(product_range,ref(partials[i]),ref(x),i*1000000,(i+1)*1000000);
    }
    for (auto& th:threads) th.join();
    for (int p : partials) answer+=p;

    auto t2 = chrono::high_resolution_clock::now();
    chrono::duration<double> d2 = t2-t1;
    cout<<"multi-thread processing time: "<<d2.count()<<" seconds"<<endl;

    answer = 0;
    t1 = chrono::high_resolution_clock::now();

    product_range(ref(answer),ref(x),0,8000000);

    t2 = chrono::high_resolution_clock::now();
    d2 = t2-t1;
    cout<<"single-thread processing time: "<<d2.count()<<" seconds"<<endl;
    return 0;
}