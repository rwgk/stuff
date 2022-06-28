#include "engine.h"

namespace vehicles {

struct vehicle {};

struct car_specs {
  static constexpr engine::tu_local_unsigned unique_id = 10;
  int power() const { return 100; }
};

}  // namespace vehicles

namespace engine {

template <>
struct specs<vehicles::vehicle> : vehicles::car_specs {};

}  // namespace engine

int car_power() { return engine::power<vehicles::vehicle>(); }
