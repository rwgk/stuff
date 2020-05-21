from __future__ import print_function

import collections

import six


def objwalk(obj, path=(), memo=None):
  # Based on https://gist.github.com/sente/1480558
  if memo is None:
    memo = set()
  if id(obj) not in memo:
    memo.add(id(obj))
    if isinstance(obj, collections.Mapping):
      for key, value in six.iteritems(obj):
        for child in objwalk(value, path + (key,), memo):
          yield child
    elif (isinstance(obj, (collections.Sequence, collections.Set)) and
          not isinstance(obj, six.string_types)):
      for index, value in enumerate(obj):
        for child in objwalk(value, path + (index,), memo):
          yield child
    else:
      yield path, obj
      if hasattr(obj, '__dict__'):
        for child in objwalk(obj.__dict__, path + ('__dict__',), memo):
          yield child


class Version(object):

  def __init__(self):
    self.major = 1
    self.minor = 2


class Info(object):

  def __init__(self):
    self.lst = [Version(), Version()]
    self.dct = {'a': Version()}
    self.version = Version()


if __name__ == '__main__':
  for path, obj in objwalk(Info()):
    print(path, repr(obj))
