import pickle


class OldStyle:

  def __init__(self):
    print 'OldStyle.__init__'

  def __getinitargs__(self):
    print 'OldStyle.__getinitargs__'
    return ()

  def __getnewargs__(self):
    print 'OldStyle.__getnewargs__'
    return ()

  def __getstate__(self):
    print 'OldStyle.__getstate__'
    return ('state',)

  def __setstate__(self, state):
    print 'OldStyle.__setstate__'


class NewStyle(object):

  def __init__(self):
    print 'NewStyle.__init__'

  def __getinitargs__(self):
    raise RuntimeError  # This will never be called.

  def __getnewargs__(self):
    print 'NewStyle.__getnewargs__'
    return ()

def NewStyle__getstate__(self):
  print 'NewStyle.__getstate__'
  return ('state',)

def NewStyle__setstate__(self, state):
  print 'NewStyle.__setstate__'


# You can use "injection" to add the getstate/setstate methods
# to Python C API objects. Works for old a new style objects.
NewStyle.__getstate__ = NewStyle__getstate__
NewStyle.__setstate__ = NewStyle__setstate__


def HaveFun():
  for style in (OldStyle, NewStyle):
    obj = style()
    print 'Have obj'
    for protocol in range(pickle.HIGHEST_PROTOCOL):
      print 'protocol', protocol
      print 'new calling dumps'
      serialized = pickle.dumps(obj, protocol=protocol)
      print 'Have serialized'
      print 'new calling loads'
      restored = pickle.loads(serialized)
      print 'Have restored'
      print


if __name__ == '__main__':
  HaveFun()
