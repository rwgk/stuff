set -e
set -x
clang++ -std=c++11 car.cc truck.cc vehicle_specs.cc && ./a.out
clang++ -std=c++11 truck.cc car.cc vehicle_specs.cc && ./a.out
rm a.out
