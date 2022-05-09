namespace engine {

namespace {
struct unique_to_translation_unit {};
}  // namespace

struct external_specs_scope {};

template <typename T>
struct specs {
  int power() const { return 0; }
};

template <typename T, typename S>
struct make_specs : specs<T> {};

template <typename T, typename U>
struct specs_scope {
  using select = external_specs_scope;
};

template <typename T, typename U>
int power() {
  return make_specs<T, typename specs_scope<T, U>::select>().power();
}

}  // namespace engine
