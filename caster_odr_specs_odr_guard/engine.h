#pragma once

#include <stdio.h>

#include <typeinfo>

namespace engine {

namespace {
struct tu_local_unsigned {
  unsigned value;
  constexpr tu_local_unsigned(unsigned v) : value(v) {}
};
}  // namespace

template <typename T>
struct specs {
  static constexpr tu_local_unsigned unique_id = 0;
  int power() const { return 0; }
};

namespace {

template <typename T>
struct specs_odr_guard : specs<T> {
  static volatile tu_local_unsigned translation_unit_local;
  specs_odr_guard() {
    if (translation_unit_local.value) {
    }
  }
};

template <typename T>
volatile tu_local_unsigned specs_odr_guard<T>::translation_unit_local = []() {
  fprintf(stdout, "MAKE_SPECS_ODR_GUARD %s %u\n", typeid(T).name(),
          specs<T>::unique_id.value);
  fflush(stdout);
  return 0;
}();

}  // namespace

template <typename T>
using make_specs = specs_odr_guard<T>;

template <typename T>
int power() {
  return make_specs<T>().power();
}

}  // namespace engine
