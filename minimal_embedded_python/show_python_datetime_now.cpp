#include <Python.h>

int main(int /*argc*/, char * /*argv*/[]) {
    const char *simple_string = "import datetime\n"
                                "print(datetime.datetime.now())\n";
    Py_Initialize();
    PyRun_SimpleString(simple_string);
    Py_Finalize();
    return 0;
}
