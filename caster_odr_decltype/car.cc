#include "engine.h"

namespace vehicles {

struct vehicle;

struct car_specs {
  int power() const { return 100; }
};

car_specs engine_select_specs(vehicle *);

}  // namespace vehicles

int car_power() { return engine::power<vehicles::vehicle>(); }
