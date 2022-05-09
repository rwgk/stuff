#include "engine.h"

namespace vehicles {

struct vehicle;

struct truck_specs {
  int power() const { return 300; }
};

}  // namespace vehicles

namespace engine {

template <>
struct make_specs<vehicles::vehicle, unique_to_translation_unit>
    : vehicles::truck_specs {};

template <>
struct specs_scope<vehicles::vehicle, unique_to_translation_unit> {
  using select = unique_to_translation_unit;
};

}  // namespace engine

int truck_power() {
  return engine::power<vehicles::vehicle, engine::unique_to_translation_unit>();
}
