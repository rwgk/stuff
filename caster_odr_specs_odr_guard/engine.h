#pragma once

#include <stdio.h>

#include <typeinfo>

namespace engine {

template <typename T>
struct specs {
  static constexpr unsigned unique_id = 0;
  int power() const { return 0; }
};

namespace {

template <typename T>
struct specs_odr_guard : specs<T> {
  static int translation_unit_local;
};

template <typename T>
int specs_odr_guard<T>::translation_unit_local = []() {
  fprintf(stdout, "MAKE_SPECS_ODR_GUARD %s %u\n", typeid(T).name(),
          specs<T>::unique_id);
  fflush(stdout);
  return 0;
}();

}  // namespace

template <typename T>
using make_specs = specs_odr_guard<T>;

template <typename T>
int power() {
  if (make_specs<T>::translation_unit_local) {
  }
  return make_specs<T>().power();
}

}  // namespace engine
