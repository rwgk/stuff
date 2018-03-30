def DoWorkInGenerator(num_work_items):
  for i in xrange(num_work_items):
    print 'G do some work here'
    yield i
    print 'G do more work here'

for i in DoWorkInGenerator(3):
  print i

################################################################################

def DoWorkWithCallback(num_work_items, callback):
  for i in xrange(num_work_items):
    print 'C do some work here'
    callback(i)
    print 'C do more work here'

def MyCallback(i):
  print i

DoWorkWithCallback(3, MyCallback)

################################################################################

class DoWorkBase(object):

  def __init__(self, num_work_items):
    for self.i in xrange(num_work_items):
      print 'B do some work here'
      self.CustomCode()
      print 'B do more work here'

  def CustomCode(self):
    raise NotImplementedError()

class DoCustomWork(DoWorkBase):

  def CustomCode(self):
    print self.i

DoCustomWork(3)

################################################################################

class DoWorkInObject(object):

  def __init__(self, i):
    print 'O do some work here'
    self.i = i

  def MoreWork(self):
    print 'O do more work here'

for i in xrange(3):
  w = DoWorkInObject(i)
  print w.i
  w.MoreWork()
