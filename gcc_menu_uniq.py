"""[Infant] Parent Menu Selections Survey."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys


def run(args):
  """Copy-paste menu from calendar to text file."""
  assert len(args) == 1
  all_items = set()
  for line in open(args[0]).read().splitlines():
    for fld in line.replace('  ', '\t').split('\t'):
      fld = fld.strip()
      while fld.startswith('*'):
        fld = fld[1:].strip()
      if fld in ('AM Snack', 'Lunch', 'PM Snack'):
        continue
      if fld:
        all_items.add(fld)
  for item in sorted(all_items):
    print(item)


if __name__ == '__main__':
  run(args=sys.argv[1:])
