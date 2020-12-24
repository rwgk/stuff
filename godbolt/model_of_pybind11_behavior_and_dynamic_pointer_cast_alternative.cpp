// https://godbolt.org/z/sdhTqY

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
  std::cout << "hello drvd_void_base" << std::endl;

  // pybind11-wrapped C++ function returns shared_ptr<base> up-cast from drvd.
  std::shared_ptr<base> shared_drvd_uc(new drvd);
  std::cout << "have shared_drvd_uc" << std::endl;
#if 0
  std::cout << "dynamic_pointer_cast<drvd>" << std::endl;
  std::shared_ptr<drvd> shared_drvd_dc = std::dynamic_pointer_cast<drvd>(shared_drvd_uc);
#elif 1
  std::cout << "dynamic_pointer_cast<void> + static_pointer_cast<drvd>" << std::endl;
  std::shared_ptr<void> ivp = std::dynamic_pointer_cast<void>(shared_drvd_uc);
  std::cout << "have ivp" << std::endl;
  std::shared_ptr<drvd> shared_drvd_dc = std::static_pointer_cast<drvd>(ivp);  // Is this well-defined?
#else
  std::cout << "pybind11 <=2.6 behavior" << std::endl;
  // intermediate void pointer.
  const void *ivp = &shared_drvd_uc;
  std::cout << "have ivp" << std::endl;
  // intermediate shared_ptr<drvd> pointer.
  const std::shared_ptr<drvd> *isdp = (const std::shared_ptr<drvd>*) ivp;  // ROOT CAUSE FOR SEGFAULT BELOW
  std::cout << "have isdp" << std::endl;
  std::shared_ptr<drvd> shared_drvd_dc = *isdp;
#endif
  std::cout << "have shared_drvd_dc" << std::endl;
  std::cout << DUMP(shared_drvd_dc.use_count()) << std::endl;
  std::cout << DUMP(shared_drvd_dc->id()) << std::endl;  // SEGFAULT HERE
}

int main() {
  std::cout << "hello main" << std::endl;
  drvd_void_base();
  return 0;
}
