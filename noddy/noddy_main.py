from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import gc
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


def show_refcount():
  print('REFCOUNT:', sys.getrefcount(noddy.Noddy))


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
  print(sys.version)
  show_refcount()
  exercise(print)
  show_refcount()
  objs = []
  for unused_index in range(10):
    objs.append(noddy.Noddy())
    show_refcount()
  del objs
  gc.collect()
  show_refcount()
  if args:
    while True:
      def noop(unused_obj):
        pass
      exercise(noop)
  show_refcount()


if __name__ == '__main__':
  run(args=sys.argv[1:])
