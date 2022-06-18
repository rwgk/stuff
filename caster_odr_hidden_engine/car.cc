#include "engine.h"

namespace vehicles {

struct vehicle;

struct car_specs {
  int power() const { return 100; }
};

}  // namespace vehicles

namespace engine {
namespace {

template <>
struct specs<vehicles::vehicle> : vehicles::car_specs {};

}  // namespace
}  // namespace engine

int car_power() { return engine::power<vehicles::vehicle>(); }
