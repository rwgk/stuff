#include "engine.h"

namespace vehicles {

struct vehicle;

struct car_specs {
  int power() const { return 100; }
};

}  // namespace vehicles

namespace engine {

template <>
struct make_specs<vehicles::vehicle, unique_to_translation_unit>
    : vehicles::car_specs {};

template <>
struct specs_scope<vehicles::vehicle, unique_to_translation_unit> {
  using select = unique_to_translation_unit;
};

}  // namespace engine

int car_power() {
  return engine::power<vehicles::vehicle, engine::unique_to_translation_unit>();
}
