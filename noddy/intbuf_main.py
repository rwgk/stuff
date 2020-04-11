from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import sys

import intbuf


class IntBufPlus(intbuf.IntBuf):
    pass


def exercise(output):
  output(intbuf)
  output(dir(intbuf))
  output(intbuf.IntBuf)
  output(dir(intbuf.IntBuf))
  output(intbuf.IntBuf())
  output(dir(intbuf.IntBuf()))
  output(IntBufPlus)
  output(dir(IntBufPlus))
  output(IntBufPlus())
  output(dir(IntBufPlus()))


def run(args):
  exercise(print)
  if args:
    while True:
      def noop(unused_obj):
        pass
      exercise(noop)


if __name__ == '__main__':
  run(args=sys.argv[1:])
