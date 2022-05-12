#include <iostream>
#include <stdexcept>

// Actual & complete Boost.Python implementation (except for the EXPORT macro).
struct error_already_set {
  virtual ~error_already_set();
};

int main() {
  std::cout << sizeof(error_already_set) << std::endl;
  std::cout << sizeof(std::exception) << std::endl;
  std::cout << sizeof(std::runtime_error) << std::endl;
}
