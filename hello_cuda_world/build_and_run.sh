#!/bin/bash
set -e
set -x
"${CC}" hello_cuda_world.c "-I${CUDA_HOME}/include" "$(ldconfig -p | grep 'libcuda\.so' | sed 's/.* => //' | head -n 1)"
./a.out
