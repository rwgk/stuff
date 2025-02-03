#! /bin/bash
THISDIR="$(dirname $0)"
for CudaVers in $*; do
  echo "NEXT CudaVers $CudaVers"
  "$THISDIR/pip_install_cuda_bindings_miniforge.sh" ManyCuda "$CudaVers" |& tee $HOME/pip_install_cuda_bindings_miniforge_many_"$CudaVers"_log_$(date "+%Y-%m-%d+%H%M%S").txt
  echo "DONE CudaVers $CudaVers"
  echo
  echo
  echo
done
