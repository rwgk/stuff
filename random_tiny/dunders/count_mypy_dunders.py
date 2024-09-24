#! /bin/bash
# https://github.com/python/mypy/blob/0a6d40b125f6b353621016d8a9022212104f7877/mypy/stubutil.py#L553-L574
for dunder in `cat ~/mypy_dunders.txt`; do
  echo -n "$dunder "
  git grep $dunder | wc -l
done
