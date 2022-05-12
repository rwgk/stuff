#include <stdexcept>

std::string error_string() {
  return "Implementation without side-effects here.";
}

struct error_already_set : std::exception {
  error_already_set() : m_py_error_indicator("Fetch here.") {}
  ~error_already_set() { /* GIL-safe dec_ref. */
  }

  void restore() { /* Restore here. */
  }

  const char* what() const noexcept override {
    m_what = m_py_error_indicator + ": " + error_string();
    return m_what.c_str();
  }

  std::string m_py_error_indicator;
  mutable std::string m_what;
};

void use_what() {
  try {
    // Now error_already_set is not a fitting name anymore.
    // throw fetched_python_error(); would be a more accurate description.
    throw error_already_set();
  } catch (error_already_set& e) {
    e.restore();
    // But we could also Fetch or Clear the error here, as needed.
    // The reason for Fetch in the error_already_set constructor is
    // something rwgk@ does not know.
  }
}

int main() { use_what(); }
