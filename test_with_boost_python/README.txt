cmake -S . -B build -DCMAKE_VERBOSE_MAKEFILE=ON
(cd build; make)
pytest -vv
