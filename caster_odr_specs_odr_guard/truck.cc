#include "engine.h"

namespace vehicles {

struct vehicle {};

struct truck_specs {
  static constexpr engine::tu_local_unsigned unique_id = 30;
  int power() const { return 300; }
};

}  // namespace vehicles

namespace engine {

template <>
struct specs<vehicles::vehicle> : vehicles::truck_specs {};

}  // namespace engine

int truck_power() { return engine::power<vehicles::vehicle>(); }
