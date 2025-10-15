#!/bin/bash
set -e
set -x
${CC} hello_cuda_world.c -I${CUDA_HOME}/include -L${CUDA_HOME}/lib64 -lcuda
LD_LIBRARY_PATH=${CUDA_HOME}/lib64 ./a.out
