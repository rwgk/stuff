from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys

import noddy


def run(args):
  assert len(args) == 0
  print(noddy)
  print(noddy.Noddy)
  print(noddy.Noddy())
  print(dir(noddy.Noddy()))


if __name__ == '__main__':
  run(args=sys.argv[1:])
