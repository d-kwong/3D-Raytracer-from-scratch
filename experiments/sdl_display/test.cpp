#include <SDL2/SDL.h>
#include <iostream>

int main() {
    if (SDL_Init(SDL_INIT_VIDEO) < 0) {
        std::cerr << "SDL init failed: " << SDL_GetError() << "\n";
        return 1;
    }

    
    SDL_Window* window = SDL_CreateWindow(
        "RGB Image Viewer",
        SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
        640, 480,
        SDL_WINDOW_SHOWN
    );

    SDL_Renderer* renderer = SDL_CreateRenderer(window, -1, SDL_RENDERER_ACCELERATED);
    SDL_Texture* texture = SDL_CreateTexture(
        renderer,
        SDL_PIXELFORMAT_RGB24,  // 24-bit RGB
        SDL_TEXTUREACCESS_STREAMING,
        640, 480
    );

    bool running = true;
    SDL_Event event;

    // Example: fill with solid color that changes on keypress
    Uint8 r = 255, g = 0, b = 0;
    std::vector<Uint8> pixels(640 * 480 * 3, 0);

    while (running) {
        while (SDL_PollEvent(&event)) {
            if (event.type == SDL_QUIT) running = false;
            if (event.type == SDL_KEYDOWN) {
                // Change color with key
                if (event.key.keysym.sym == SDLK_r) { r = 255; g = 0; b = 0; }
                if (event.key.keysym.sym == SDLK_g) { r = 0; g = 255; b = 0; }
                if (event.key.keysym.sym == SDLK_b) { r = 0; g = 0; b = 255; }
            }
        }

        // Update pixel buffer with chosen color
        for (int i = 0; i < pixels.size(); i += 3) {
            pixels[i]   = r; // R
            pixels[i+1] = g; // G
            pixels[i+2] = b; // B
        }

        SDL_UpdateTexture(texture, nullptr, pixels.data(), 640 * 3);
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
