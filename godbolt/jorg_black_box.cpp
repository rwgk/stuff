// https://godbolt.org/z/eTEvG3

#include <iostream>
#include <memory>
#include <typeindex>

#define DUMP(expr) #expr " = " << (expr)

struct base {
  base() : base_id{100} {}
  virtual ~base() = default;
  virtual int const id() { return base_id; }
  int base_id;
};
struct monkeywrench {
  virtual int const monkey_id() { return 150; }
  virtual ~monkeywrench() = default;
};
struct drvd : monkeywrench, base {
  int const id() override { return 2 * base_id; }
};

struct BlackBox {
  std::shared_ptr<void> magicptr;
  std::type_index magictype;

  BlackBox() : magictype(typeid(void)) {}
  template <typename T>
  BlackBox(std::shared_ptr<T> in)                      //
      : magicptr(std::static_pointer_cast<void>(in)),  //
        magictype(typeid(T)) {}

  template <typename T>
  std::shared_ptr<T> get() const {
    if (magictype == std::type_index(typeid(T))) {
      return std::static_pointer_cast<T>(magicptr);
    } else
      return {};
  }
};

void drvd_void_base() {
  std::cout << "hello drvd_void_base" << '\n';
  BlackBox b;

  // pybind11-wrapped C++ function returns shared_ptr<base> up-cast from drvd.
  {
    std::shared_ptr<base> shared_base_uc(new base);
    std::cout << "In:  " << DUMP(shared_base_uc->id()) << '\n';
    b = shared_base_uc;

    std::shared_ptr<base> shared_base_dc = b.get<base>();
    std::cout << "Out: " << DUMP(shared_base_dc->id()) << '\n';
  }
  {
    std::shared_ptr<base> shared_base_uc(new drvd);
    std::cout << "In:  " << DUMP(shared_base_uc->id()) << '\n';
    b = shared_base_uc;

    std::shared_ptr<base> shared_base_dc = b.get<base>();
    std::cout << "Out: " << DUMP(shared_base_dc->id()) << '\n';
  }
  {
    std::shared_ptr<drvd> shared_drvd_uc(new drvd);
    std::cout << "In:  " << DUMP(shared_drvd_uc->id()) << '\n';
    b = shared_drvd_uc;

    std::shared_ptr<drvd> shared_drvd_dc = b.get<drvd>();
    std::cout << "Out: " << DUMP(shared_drvd_dc->id()) << '\n';
  }
}

void bad_cast() {
  std::cout << "uh-oh bad_cast" << '\n';
  BlackBox b;

  // pybind11-wrapped C++ function returns shared_ptr<base> up-cast from drvd.

  {
    std::shared_ptr<base> shared_base_uc(new drvd);
    std::cout << "In:  " << DUMP(shared_base_uc->id()) << '\n';
    b = shared_base_uc;

    std::cout << std::flush;

    std::shared_ptr<drvd> shared_drvd_dc = b.get<drvd>();
    if (shared_drvd_dc) {
      std::cout << "Out: " << DUMP(shared_drvd_dc->id()) << '\n';
    } else {
      std::cout << "Out: nullptr, sorry!\n";
    }
  }
}

int main() {
  std::cout << "hello main" << '\n';
  drvd_void_base();
  bad_cast();
  return 0;
}
