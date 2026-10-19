CXX ?= c++
CPPFLAGS ?=
CXXFLAGS ?= -O2 -std=c++17 -Wall -Wextra -Wpedantic
LDLIBS += -pthread

.PHONY: all test clean
all: build/raytracer

build:
	mkdir -p build

build/raytracer: src/main.cpp src/raytracer.hpp | build
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) src/main.cpp -o $@ $(LDLIBS)

build/test_geometry: tests/test_geometry.cpp src/raytracer.hpp | build
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) tests/test_geometry.cpp -o $@ $(LDLIBS)

test: build/raytracer build/test_geometry
	./build/test_geometry
	python3 tests/test_cli.py ./build/raytracer

clean:
	rm -rf build
