#! /bin/bash
# cd cuda-python/cuda_bindings
CUV=12.0
CEN=cpcv120
eval "$("$HOME/miniforge3/bin/conda" shell.bash hook)"
set -e
set -x
conda create --yes -n "$CEN" python=3.12 cuda-cudart-dev cuda-cudart cuda-nvrtc-dev cuda-nvrtc cuda-profiler-api cuda-nvcc libnvjitlink libnvjitlink-dev cuda-version="$CUV"
set +x
conda activate "$CEN"
set -x
export CUDA_PYTHON_PARALLEL_LEVEL=64 && export CUDA_HOME=$CONDA_PREFIX/targets/x86_64-linux
python -m venv "$CEN"Venv
set +x
. "$CEN"Venv/bin/activate
set -x
pip install --upgrade pip
pip install -r requirements.txt
# SKIP
# BUILDING WHEEL
pip install -v --force-reinstall ./dist/cuda_bindings-*.whl
export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}:${CUDA_HOME}/lib:${CUDA_HOME}/nvvm/lib64"
pytest -v tests/
