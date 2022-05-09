set -e
set -x
clang++ -std=c++11 unknown.cc car.cc truck.cc vehicle_specs.cc && ./a.out
clang++ -std=c++11 unknown.cc truck.cc car.cc vehicle_specs.cc && ./a.out
rm a.out
