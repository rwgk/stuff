#! /bin/bash
eval "$("$HOME/miniforge3/bin/conda" shell.bash hook)"
set -x
conda create --yes -n ScratchCuda128 python=3.12 cuda-cudart-dev cuda-cudart cuda-nvrtc-dev cuda-nvrtc cuda-profiler-api cuda-nvcc libnvjitlink libnvjitlink-dev cuda-version=12.8
set +x
conda activate ScratchCuda128
set -x
mkdir ScratchCuda128
cd ScratchCuda128
git clone https://github.com/NVIDIA/cuda-python.git
cd cuda-python/cuda_bindings/
python -m venv ScratchCuda128
. ScratchCuda128/bin/activate
pip install --upgrade pip
pip install -r requirements.txt 
export CUDA_PYTHON_PARALLEL_LEVEL=64 && export CUDA_HOME=$CONDA_PREFIX/targets/x86_64-linux
ls -l "$CUDA_HOME"
pip install -v --force-reinstall --upgrade .
pytest -v tests/
