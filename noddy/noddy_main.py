from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys

import noddy


try:
  class NoddyPlus(noddy.Noddy):
    pass
except TypeError as e:
  print()
  print('WARNING:', e)
  print()
  NoddyPlus = None


def exercise(output):
  output(noddy)
  output(dir(noddy))
  output(noddy.Noddy)
  output(dir(noddy.Noddy))
  output(noddy.Noddy())
  output(dir(noddy.Noddy()))
  if NoddyPlus is not None:
    output(NoddyPlus)
    output(dir(NoddyPlus))
    output(NoddyPlus())
    output(dir(NoddyPlus()))


def run(args):
  exercise(print)
  if args:
    while True:
      def noop(unused_obj):
        pass
      exercise(noop)


if __name__ == '__main__':
  run(args=sys.argv[1:])
