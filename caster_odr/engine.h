namespace engine {

#ifdef USE_UNIQUE_TO_TRANSLATION_UNIT
namespace {
struct unique_to_translation_unit {};
}  // namespace

template <typename T, typename = unique_to_translation_unit>
#else
template <typename T>
#endif
struct specs;

#ifdef USE_UNIQUE_TO_TRANSLATION_UNIT
template <typename T, typename = unique_to_translation_unit>
#else
template <typename T>
#endif
int power() {
  return specs<T>().power();
}

}  // namespace engine
