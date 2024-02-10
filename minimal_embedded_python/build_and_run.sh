set -x
clang++ -std=c++11 -I/usr/include/python3.11 -g -O0 show_python_datetime_now.cpp -o show_python_datetime_now -lpython3.11
./show_python_datetime_now
