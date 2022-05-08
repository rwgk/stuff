#include "engine.h"

namespace engine {

template <>
struct specs<short> {
  int power() const { return 100; }
};

template <>
struct specs<long> {
  int power() const { return 200; }
};

}  // namespace engine

int short_car_power() { return engine::power<short>(); }
int long_car_power() { return engine::power<long>(); }
