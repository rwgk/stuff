#include "engine.h"

namespace vehicles {

struct vehicle;

struct truck_specs {
  int power() const { return 300; }
};

}  // namespace vehicles

namespace engine {
namespace {

template <>
struct specs<vehicles::vehicle> : vehicles::truck_specs {};

}  // namespace
}  // namespace engine

int truck_power() { return engine::power<vehicles::vehicle>(); }
