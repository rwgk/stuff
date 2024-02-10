set -x
rm -f hello_extenstion_module.so
clang++ -std=c++11 -I/usr/include/python3.11 -shared -fPIC -g -O0 hello_extenstion_module.cpp -o hello_extenstion_module.so
python3 use_hello_extenstion_module.py
