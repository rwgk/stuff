#include "engine.h"

namespace engine {

template <>
struct specs<short> {
  int power() const { return 300; }
};

template <>
struct specs<long> {
  int power() const { return 400; }
};

}  // namespace engine

int short_truck_power() { return engine::power<short>(); }
int long_truck_power() { return engine::power<long>(); }
