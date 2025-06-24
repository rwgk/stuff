#!/bin/bash
set +e
set -x
printenv
git status --ignored
nvcc --version
echo "==== $(date +"%F %T") BEFORE make setup-env ===="
make setup-env
echo "==== $(date +"%F %T")  AFTER make setup-env ===="
source /wrk/pytorch/venv/bin/activate
echo "==== $(date +"%F %T") BEFORE pip install -r requirements.txt ===="
pip install -r requirements.txt
echo "==== $(date +"%F %T")  AFTER pip install -r requirements.txt ===="
pip show pybind11
echo "==== $(date +"%F %T") BEFORE python setup.py develop ===="
python setup.py develop
echo "==== $(date +"%F %T")  AFTER python setup.py develop ===="
