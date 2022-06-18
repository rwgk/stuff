#pragma once

namespace engine {
namespace {

template <typename T>
struct specs {
  int power() const { return 0; }
};

template <typename T>
using make_specs = specs<T>;

template <typename T>
int power() {
  return make_specs<T>().power();
}

}  // namespace
}  // namespace engine
