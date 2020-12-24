// https://godbolt.org/z/8873Wd

#include <iostream>
#include <memory>

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

void drvd_void_base() {
  // pybind11-wrapped C++ function returns shared_ptr<base> up-cast from drvd.
  std::shared_ptr<base> shared_drvd_uc(new drvd);
  std::shared_ptr<void> ivp = std::dynamic_pointer_cast<void>(shared_drvd_uc);
  std::shared_ptr<drvd> shared_drvd_dc = std::static_pointer_cast<drvd>(ivp);
  // SEGFAULT:
  // std::shared_ptr<base> shared_drvd_dc_uc = std::static_pointer_cast<base>(ivp);
  // Can upcast only from std::shared_ptr<drvd>:
  std::shared_ptr<base> shared_drvd_dc_uc = shared_drvd_dc;
  std::cout << DUMP(shared_drvd_dc_uc->id()) << '\n';
}

int main() {
  drvd_void_base();
  return 0;
}
