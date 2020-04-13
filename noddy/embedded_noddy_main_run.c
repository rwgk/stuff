/* Attempted noddy_heaptype leak test but it turns out Py_Finalize does
   NOT clean up all memory even if immediately following Py_Initialize.
   See "Bugs and caveats" note here:
   https://docs.python.org/2/c-api/init.html#c.Py_Finalize
   Leaks observed with Python 2.7.17 and 3.7.6.
 */

#include <Python.h>

int main(int argc, char* argv[]) {
  const char* simple_string =
      "from __future__ import print_function\n"
      "import sys\n"
      "sys.path.insert(0, '.')\n"
      "from noddy_main import run\n"
      "run([])\n";
  int endless = 0;
  if (argc > 1) {
    int mode = argv[1][0];
    if (mode == 'n' || mode == 'N') {
      simple_string = "";
    } else if (mode == 'v' || mode == 'V') {
      simple_string =
          "from __future__ import print_function\n"
          "import sys\n"
          "print(sys.version)\n";
    } else if (mode == 't' || mode == 'T') {
      simple_string =
          "from __future__ import print_function\n"
          "from time import time, ctime\n"
          "print('Today is', ctime(time()))\n";
    }
    if (!islower(mode)) {
      endless = 1;
    }
  }
  printf("%s\n", simple_string);
  printf("endless: %d\n\n", endless);
#if PY_MAJOR_VERSION >= 3
  wchar_t progname[8 * 1024];
  const size_t csize = strlen(argv[0]) + 1;
  if (csize > sizeof(progname) * sizeof(wchar_t)) {
    printf("FATAL: progname too long");
    return 1;
  }
  mbstowcs(progname, argv[0], csize);
#else
  char* progname = argv[0];
#endif
  Py_SetProgramName(progname); /* optional but recommended */
  while (1) {
    Py_Initialize();
    if (simple_string[0]) {
      PyRun_SimpleString(simple_string);
    }
    Py_Finalize();
    if (!endless) break;
  }
  return 0;
}
