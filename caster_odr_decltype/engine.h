namespace engine {

#ifdef USE_UNIQUE_TO_TRANSLATION_UNIT

namespace {
struct unique_to_translation_unit {};
}  // namespace

#define TTT template <typename T, typename U = unique_to_translation_unit>

#else

#define TTT template <typename T>

#endif

TTT using make_specs = decltype(engine_select_specs(static_cast<T *>(nullptr)));

TTT int power() { return make_specs<T>().power(); }

}  // namespace engine
