#! /bin/bash
if [ $# -ne 2 ]; then
  echo "usage: $(basename "$0") CondaEnvNamePrefix 12.x"
  exit 1
fi
CEN="$(echo "$1"_"$2" | tr . _)"
eval "$("$HOME/miniforge3/bin/conda" shell.bash hook)"
set -e
set -x
conda create --yes -n "$CEN" python=3.12 cuda-cudart-dev cuda-cudart cuda-nvrtc-dev cuda-nvrtc cuda-profiler-api cuda-nvcc libnvjitlink libnvjitlink-dev cuda-version="$2"
set +x
conda activate "$CEN"
set -x
mkdir "$CEN"
cd "$CEN"
git clone https://github.com/NVIDIA/cuda-python.git
cd cuda-python/cuda_bindings/
python -m venv "$CEN"Venv
set +x
. "$CEN"Venv/bin/activate
set -x
pip install --upgrade pip
pip install -r requirements.txt
export CUDA_PYTHON_PARALLEL_LEVEL=64 && export CUDA_HOME=$CONDA_PREFIX/targets/x86_64-linux
ls -l "$CUDA_HOME"
pip install -v --force-reinstall --upgrade .
pytest -v tests/
