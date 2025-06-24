export CUDA_HOME="/usr/local/cuda"
export PATH="$CUDA_HOME/bin:$PATH"
nvcc --version
wipe_tmp_user_caches
use_tmp_user_caches
