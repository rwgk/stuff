#include <iostream>
#include <stdexcept>

std::string error_string() {
  return "Implementation without side-effects here.";
}

struct error_already_set : std::exception {
  const char* what() const noexcept override {
    m_what = error_string();
    return m_what.c_str();
  }
  mutable std::string m_what;
};

void use_error_string() {
  try {
    throw error_already_set();
  } catch (const error_already_set&) {
    std::cout << error_string() << std::endl;
  }
}

void use_what() {
  try {
    throw error_already_set();
  } catch (const error_already_set& e) {
    // Is enabling e.what() worth the m_what overhead?
    std::cout << e.what() << std::endl;
  }
}

int main() {
  use_error_string();
  use_what();
}
