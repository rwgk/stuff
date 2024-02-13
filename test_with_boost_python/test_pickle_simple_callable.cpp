#include <boost/python.hpp>

namespace {

int simple_callable() { return 723; }

}

BOOST_PYTHON_MODULE(test_pickle_simple_callable) {
    namespace py = boost::python;

    py::def("simple_callable", simple_callable);
}
