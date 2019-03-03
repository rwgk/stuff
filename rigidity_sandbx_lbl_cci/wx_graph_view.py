from __future__ import division
from __future__ import generators

import gltbx.wx_viewer
from scitbx.array_family import flex
import scitbx.math
import wx
import sys, os

class show_tripod(gltbx.wx_viewer.show_points_and_lines_mixin):

  def __init__(self, *args, **keyword_args):
    super(show_tripod, self).__init__(*args, **keyword_args)
    self.flag_show_minimum_covering_sphere = False
    self.flag_show_rotation_center = False
    p0 = matrix.col((1,1,0))
    p1 = p0 + matrix.col((1,0,0))
    p2 = p0 + matrix.col((0,2,0))
    p3 = p0 + matrix.col((0,0,3))
    self.points = flex.vec3_double([p0, p1, p2])
    self.labels = ["p0", "p1", "p2"]
    self.line_i_seqs = [(0,1),(1,2),(2,0)]
    d0 = abs(p3-p0)
    d1 = abs(p3-p1)
    d2 = abs(p3-p2)
    from tripod import tripod_node
    tripod = tripod_node(
      points=[p0, p1, p2],
      distances=[d0, d1, d2],
      p3_sign=1)
    self.labels.append("p3+")
    self.points.append(tripod.p3)
    self.line_i_seqs.extend([(0,3),(1,3),(2,3)])
    tripod = tripod_node(
      points=[p0, p1, p2],
      distances=[d0, d1, d2],
      p3_sign=-1)
    self.labels.append("p3-")
    self.points.append(tripod.p3)
    self.line_i_seqs.extend([(0,4),(1,4),(2,4)])
    s = scitbx.math.minimum_covering_sphere_3d(points=self.points)
    self.minimum_covering_sphere = s
    self.labels_display_list = None
    self.lines_display_list = None
    self.points_display_list = None

class show_tripod_refine(gltbx.wx_viewer.show_points_and_lines_mixin):

  def __init__(self, *args, **keyword_args):
    super(show_tripod_refine, self).__init__(*args, **keyword_args)
    self.flag_show_minimum_covering_sphere = False
    self.flag_show_rotation_center = False
    self.points = flex.vec3_double()
    self.labels = []
    self.line_i_seqs = []
    self.refinery_call_back_counter = 0
    from tripod import exercise_random
    exercise_random(refinery_call_back=self.refinery_call_back)
    s = scitbx.math.minimum_covering_sphere_3d(points=self.points)
    self.minimum_covering_sphere = s
    self.labels_display_list = None
    self.lines_display_list = None
    self.points_display_list = None

  def refinery_call_back(self, tripod, homes):
    self.refinery_call_back_counter += 1
    rcc = self.refinery_call_back_counter
    print "refinery_call_back", rcc
    if (rcc >= 8):
      nppts = self.points.size()
      for p in tripod.points: self.points.append(p)
      self.labels.extend(["p%d.%d" % (i, rcc) for i in xrange(3)])
      self.line_i_seqs.extend(
        [(nppts+i,nppts+j) for i,j in [(0,1),(1,2),(2,0)]])
      if (tripod.p3 is not None):
        self.points.append(tripod.p3)
        self.labels.append("p3.%d" % rcc)
        self.line_i_seqs.extend(
          [(nppts+i,nppts+j) for i,j in [(0,3),(1,3),(2,3)]])
      else:
        for p,d in zip(tripod.points, tripod.distances):
          self.spheres.append((p,d))

class show_pdb(gltbx.wx_viewer.show_points_and_lines_mixin):

  def __init__(self, *args, **keyword_args):
    super(show_pdb, self).__init__(*args, **keyword_args)
    self.flag_show_minimum_covering_sphere = False
    self.flag_show_rotation_center = False

  def set_points_and_lines(self, processed_pdb):
    atom_attributes_list = processed_pdb.atom_attributes_list
    if (0):
      self.labels.extend([atom.pdb_format() for atom in atom_attributes_list])
    else:
      self.labels.extend(["%d %s" % (i,atom.name)
        for i,atom in enumerate(atom_attributes_list)])
    if (len(self.labels) > 30):
      self.flag_show_labels = False
    self.points.extend(flex.vec3_double([atom.coordinates
      for atom in atom_attributes_list]))
    s = scitbx.math.minimum_covering_sphere_3d(points=self.points)
    self.minimum_covering_sphere = s
    self.labels_display_list = None
    self.points_display_list = None
    #
    for g1 in processed_pdb.primary_graphs:
      for i_seqs in g1:
        self.line_i_seqs.append(i_seqs)
        self.line_colors[tuple(sorted(i_seqs))] = (1,0,0)
    for g2 in processed_pdb.secondary_graphs:
      for i_seqs in g2:
        self.line_i_seqs.append(i_seqs)
        self.line_colors[tuple(sorted(i_seqs))] = (0,1,0)
    self.lines_display_list = None

class show_msd(gltbx.wx_viewer.show_points_and_lines_mixin):

  def __init__(self, *args, **keyword_args):
    super(show_msd, self).__init__(*args, **keyword_args)
    self.flag_show_minimum_covering_sphere = False
    self.flag_show_rotation_center = False
    self.points = flex.vec3_double()
    self.labels = []
    self.line_i_seqs = []

  def set_points_and_lines(self, processed_msd):
    for atom in processed_msd.atom_list:
      self.labels.append(atom.label)
      self.points.append(atom.site)
    if (len(self.labels) > 30):
      self.flag_show_labels = False
    if (processed_msd.bonds_forward is None):
      for i_seq,bond_list in enumerate(processed_msd.bond_lists):
        for bond in bond_list:
          self.line_i_seqs.append((i_seq,bond.j_seq))
    else:
      self.line_i_seqs = processed_msd.bonds_forward + processed_msd.bonds_back
      for i_seqs in processed_msd.bonds_forward:
        self.line_colors[tuple(sorted(i_seqs))] = (0,1,0)
      for i_seqs in processed_msd.bonds_back:
        self.line_colors[tuple(sorted(i_seqs))] = (1,0,0)
    for g in processed_msd.secondary_graphs:
      for i_seqs in g:
        self.line_i_seqs.append(i_seqs)
        self.line_colors[tuple(sorted(i_seqs))] = (0,0,1)
    for e in processed_msd.potential_implicit_edges:
      self.line_i_seqs.append(e)
      self.line_colors[tuple(sorted(e))] = (0.5,0.5,0.5)
    for e in processed_msd.hinges:
      self.line_colors[tuple(sorted(e))] = (1,1,1)
    if (len(self.points) > 1):
      s = scitbx.math.minimum_covering_sphere_3d(points=self.points)
    else:
      s = scitbx.math.sphere_3d(center=self.points[0], radius=1)
    self.minimum_covering_sphere = s
    self.labels_display_list = None
    self.lines_display_list = None
    self.points_display_list = None

class tab_stop_driver(object):

  def __init__(self, processed_msd, co, show_points_and_lines_mixin):
    self.processed_msd = processed_msd
    self.co = co
    self.show_points_and_lines_mixin = show_points_and_lines_mixin
    self.set_minimum_covering_sphere()
    self.restart()

  def restart(self):
    self.construction = self.construction_generator()

  def set_minimum_covering_sphere(self):
    points = flex.vec3_double()
    for atom in self.processed_msd.atom_list:
      points.append(atom.site)
    if (len(points) > 1):
      s = scitbx.math.minimum_covering_sphere_3d(points=points)
    else:
      if (len(points) == 0):
        center = (0,0,0)
      else:
        center = points[0]
      s = scitbx.math.sphere_3d(center=center, radius=1)
    if (self.co.dynamics):
      s = scitbx.math.sphere_3d(center=s.center(), radius=3*s.radius())
    self.show_points_and_lines_mixin.minimum_covering_sphere = s
    if (len(points) > 30):
      self.show_points_and_lines_mixin.flag_show_labels = False

  def construction_generator(self):
    if (self.co.dynamics):
      return self.construction_generator_dynamics()
    else:
      return self.construction_generator_edges()

  def construction_generator_edges(self):
    mixin = self.show_points_and_lines_mixin
    atom_list = self.processed_msd.atom_list
    edge_lists = self.processed_msd.edge_lists()
    atom_vertex_indices = [None] * len(atom_list)
    for i_atom in xrange(len(atom_list)):
      if (atom_vertex_indices[i_atom] is not None): continue
      while True:
        atom = atom_list[i_atom]
        i_vertex = len(mixin.points)
        atom_vertex_indices[i_atom] = i_vertex
        mixin.labels.append(atom.label)
        mixin.points.append(atom.site)
        print "vertex:", i_atom, atom.label
        yield
        next_i_atom = None
        i_atom_edge_count = 0
        for j_atom in edge_lists[i_atom]:
          j_vertex = atom_vertex_indices[j_atom]
          if (j_vertex is None):
            if (next_i_atom is None):
              next_i_atom = j_atom
          else:
            if (i_atom_edge_count == 3):
              print "SEARCH FOR REPLACEMENT EDGE"
            elif (i_atom_edge_count > 3):
              print "AVOID THIS BY DOING SOMETHING ABOVE"
            mixin.line_i_seqs.append(tuple(sorted((i_vertex,j_vertex))))
            i_atom_edge_count += 1
            print "edge:", tuple(sorted((i_atom,j_atom)))
            yield
        if (next_i_atom is None):
          break
        i_atom = next_i_atom

  def construction_generator_dynamics(self):
    import dynamics_prototype
    mixin = self.show_points_and_lines_mixin
    for atom in self.processed_msd.atom_list:
      mixin.labels.append(atom.label)
    for i,j in self.processed_msd.edge_iterator():
      mixin.line_i_seqs.append(tuple(sorted((i,j))))
    stepper = dynamics_prototype.stepper(
      comp=self.processed_msd,
      interleaved_minimization_steps=self.co.interleaved_minimization_steps)
    while True:
      stepper.next()
      mixin.points.clear()
      for site in stepper.sites_cart:
        mixin.points.append(site)
      yield

  def next(self):
    try: self.construction.next()
    except StopIteration:
      print "No more objects to add."
      return False
    return True

class show_msd_tab_stop(gltbx.wx_viewer.show_points_and_lines_mixin):

  def __init__(self, *args, **keyword_args):
    super(show_msd_tab_stop, self).__init__(*args, **keyword_args)
    self.flag_show_labels = True
    self.flag_show_minimum_covering_sphere = False
    self.flag_show_rotation_center = False
    self.reset_points_and_lines()

  def reset_points_and_lines(self):
    self.points = flex.vec3_double()
    self.labels = []
    self.line_i_seqs = []

  def driver_init(self, processed_msd, co):
    self.tab_stop_driver = tab_stop_driver(
      processed_msd=processed_msd,
      co=co,
      show_points_and_lines_mixin=self)

  def tab_callback(self, shift_down):
    if (shift_down):
      print "Clearing all points and lines."
      self.reset_points_and_lines()
      self.tab_stop_driver.restart()
      self.reset_display_lists()
      self.OnRedraw()
    elif (self.tab_stop_driver.next()):
      self.reset_display_lists()
      self.OnRedraw()

  def reset_display_lists(self):
    self.labels_display_list = None
    self.lines_display_list = None
    self.points_display_list = None

class App(gltbx.wx_viewer.App):

  def __init__(self, args):
    import as_graph
    command_line = as_graph.process_command_line_args(args=args)
    args = command_line.args
    co = command_line.options
    assert len(args) in [0, 1]
    self.co = co
    self.processed_pdb = None
    self.processed_msd = None
    if (len(args) == 1):
      if (0 and os.path.isfile(args[0])):
        import pdb_as_graphs
        self.processed_pdb = pdb_as_graphs.process(file_name=args[0])
        self.processed_pdb.as_graph()
      else:
        self.processed_msd = as_graph.process(
          code=args[0],
          attach_inverse_pivots=co.attach_inverse,
          delete_expressions=co.delete,
          add_edge_expressions=co.add_edge)
    super(App, self).__init__()

  def init_view_objects(self):
    if (self.processed_pdb is not None):
      self.view_objects = show_pdb(
        self.frame, -1, wx.Point(0,0), self.default_size)
      self.view_objects.set_points_and_lines(processed_pdb=self.processed_pdb)
    elif (self.processed_msd is not None):
      if (not self.co.tab_stop):
        self.processed_msd.as_graph_given_command_line_options(co=self.co)
        self.view_objects = show_msd(
          self.frame, id=-1, pos=wx.Point(0,0), size=self.default_size)
        self.view_objects.set_points_and_lines(
          processed_msd=self.processed_msd)
      else:
        self.view_objects = show_msd_tab_stop(
          self.frame, id=-1, pos=wx.Point(0,0), size=self.default_size)
        self.view_objects.driver_init(
          processed_msd=self.processed_msd,
          co=self.co)
    else:
      self.view_objects = show_tripod_refine(
        self.frame, -1, wx.Point(0,0), self.default_size)
    box = wx.BoxSizer(wx.VERTICAL)
    box.Add(self.view_objects, wx.EXPAND, wx.EXPAND)
    self.frame.SetSizer(box)
    box.SetSizeHints(self.frame)

def run(args):
  App(args).MainLoop()

if (__name__ == "__main__"):
  run(sys.argv[1:])
