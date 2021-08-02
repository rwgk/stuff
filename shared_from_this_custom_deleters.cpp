/* clang++ -std=c++11 shared_from_this_custom_deleters.cpp && a.out

   Simple experiment, to show that `.shared_from_this()` ~only retrieves
   the first `shared_ptr` created for a given pointee. (See obj1_reset() for
   a more complete story.)
 */

#include <iostream>
#include <memory>

template <typename T>
struct labeled_delete {
  std::string label;
  explicit labeled_delete(const std::string& label) : label{label} {}
  void operator()(T* raw_ptr) {
    std::cout << "labeled_delete::operator() " << label << std::endl;
    if (label != "SkipDelete") {
      delete raw_ptr;
    }
  }
};

struct Atype : std::enable_shared_from_this<Atype> {};

#define SHOW_USE_COUNTS                                              \
  std::cout << "obj1, obj2 use_counts: " << obj1.use_count() << ", " \
            << obj2.use_count() << std::endl;

void obj1_owns() {
  std::cout << "\nobj1_owns()" << std::endl;
  std::shared_ptr<Atype> obj1(new Atype, labeled_delete<Atype>("1st"));
  std::shared_ptr<Atype> obj2(obj1.get(), labeled_delete<Atype>("SkipDelete"));
  SHOW_USE_COUNTS
  auto sft1 = obj1->shared_from_this();
  SHOW_USE_COUNTS
  auto sft2 = obj2->shared_from_this();
  SHOW_USE_COUNTS
}
/* Expected output:
obj1_owns()
obj1, obj2 use_counts: 1, 1
obj1, obj2 use_counts: 2, 1
obj1, obj2 use_counts: 3, 1
labeled_delete::operator() SkipDelete
labeled_delete::operator() 1st
*/

void obj2_owns() {
  std::cout << "\nobj2_owns()" << std::endl;
  std::shared_ptr<Atype> obj1(new Atype, labeled_delete<Atype>("SkipDelete"));
  std::shared_ptr<Atype> obj2(obj1.get(), labeled_delete<Atype>("2nd"));
  SHOW_USE_COUNTS
  auto sft1 = obj1->shared_from_this();
  SHOW_USE_COUNTS
  auto sft2 = obj2->shared_from_this();
  SHOW_USE_COUNTS
}
/* Expected output:
obj2_owns()
obj1, obj2 use_counts: 1, 1
obj1, obj2 use_counts: 2, 1
obj1, obj2 use_counts: 3, 1
labeled_delete::operator() 2nd
labeled_delete::operator() SkipDelete
*/

void obj1_reset() {
  std::cout << "\nobj1_reset()" << std::endl;
  std::shared_ptr<Atype> obj1(new Atype, labeled_delete<Atype>("SkipDelete"));
  std::shared_ptr<Atype> obj2(obj1.get(), labeled_delete<Atype>("ThisDeletes"));
  obj1->shared_from_this();
  obj2->shared_from_this();
  obj1.reset();
  bool got_bad_weak_ptr = false;
  try {
    obj2->shared_from_this();
  } catch (const std::bad_weak_ptr&) {
    got_bad_weak_ptr = true;
  }
  std::cout << "got_bad_weak_ptr: " << got_bad_weak_ptr << std::endl;
  std::shared_ptr<Atype> obj3(obj2.get(), labeled_delete<Atype>("SkipDelete"));
  // Working again based on the shared_ptr that was created after obj1 was
  // reset:
  obj2->shared_from_this();
  //obj3.reset();
  obj2->weak_from_this().reset();
  got_bad_weak_ptr = false;
  try {
    obj2->shared_from_this();
  } catch (const std::bad_weak_ptr&) {
    got_bad_weak_ptr = true;
  }
  std::cout << "got_bad_weak_ptr: " << got_bad_weak_ptr << std::endl;
  //std::weak_ptr<Atype> obj2_wp(obj2);
  //obj2->weak_from_this().swap(obj2_wp);
}
/* Expected output:
obj1_reset()
labeled_delete::operator() SkipDelete
got_bad_weak_ptr: 1
labeled_delete::operator() SkipDelete
labeled_delete::operator() ThisDeletes
*/

int main() {
  obj1_owns();
  obj2_owns();
  obj1_reset();
  return 0;
}
