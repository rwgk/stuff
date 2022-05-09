#include "engine.h"

namespace vehicles {

struct vehicle;

struct truck_specs {
  int power() const { return 300; }
};

truck_specs engine_select_specs(vehicle *);

}  // namespace vehicles

int truck_power() { return engine::power<vehicles::vehicle>(); }
