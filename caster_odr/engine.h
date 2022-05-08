namespace engine {

#ifdef USE_TRANSLATION_UNIT_TAG
namespace {
struct translation_unit_tag {};
}  // namespace

template <typename T, typename = translation_unit_tag>
#else
template <typename T>
#endif
struct specs;

#ifdef USE_TRANSLATION_UNIT_TAG
template <typename T, typename = translation_unit_tag>
#else
template <typename T>
#endif
int power() {
  return specs<T>().power();
}

}  // namespace engine
