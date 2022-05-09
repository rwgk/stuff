#include "engine.h"

namespace vehicles {

struct vehicle;

}

int unknown_power() {
  return engine::power<vehicles::vehicle, engine::unique_to_translation_unit>();
}
