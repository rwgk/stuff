from __future__ import division
from __future__ import generators
import constrained_graph_3d as cg3d
import nodes_3d
from tripod import tripod_node
import rigidity_practical
from cctbx import crystal
import cctbx.crystal.direct_space_asu
from scitbx.graph.rigidity import gcd, construct_integer_rigidity_matrix, \
                                  determine_degrees_of_freedom
from scitbx.array_family import flex
from scitbx import matrix
import scitbx.math
from libtbx.option_parser import libtbx_option_parser
from libtbx import easy_pickle
from libtbx.utils import format_cpu_times
from libtbx.test_utils import approx_equal
import libtbx.load_env
from itertools import count
import random
import math
import traceback
import sys, os

sys.setrecursionlimit(100000)

if (1):
  random.seed(0)
  flex.set_random_seed(0)

# original pickle files:
#   /net/cci-filer1/vol1/tmp/nigel/msd_exp_comps
#   /net/cci-filer1/vol1/tmp/nigel/msd_exp

"""
problem cases: CB5 CLF CUZ FS4 TBR

... A node that leads to degrees of freedom < 0
... Detach completely?
... Find three closest node with degrees of freedom > 0

... If a distance constraint (d.c.) leads to a dof < 0 for a given node p
...   inspect the three nodes fixing p
...   degrees of freedom > 0?
...   replace original d.c. with alternative d.c.

If degrees of freedom of a node is less than 1, find all directly
connected nodes and mark the whole groups as rigid?

Test: isolate the group, is the number of degrees of freedom exaclty
  3 if there is just one node
  5 if there are two nodes
  6 if there are three or more nodes in the group?

Treat triangles as special:
  1 triangle:
      3 nodes, 3 dof (rotations)
  2 triangles with one common edge:
      4 nodes, 4 dof (3 for 1st triangle, 1 for 2nd)
  loop of n triangles (one node common to all):
      n+1 nodes, 3 dof (rotations)
"""

if (os.name == "nt"):
  dir_pickles = libtbx.env.under_build("probl")
else:
  dir_pickles = "/net/chevy/raid1/rwgk/nigel_msd_exp_comps"
if (not os.path.isdir(dir_pickles)):
  dir_pickles = None

golden_ratio = (1 + 5**0.5) / 2

def degrees_as_rad(v): return v * math.pi / 180

class atom(object):

  def __init__(self, label, element, site):
    self.label = label
    self.element = element
    self.site = site

class bond(object):

  def __init__(self, j_seq, distance_ideal):
    self.j_seq = j_seq
    self.distance_ideal = distance_ideal

class angle(object):

  def __init__(self, i_seqs, angle_ideal):
    self.i_seqs = i_seqs
    self.angle_ideal = angle_ideal

class dihedral(object):

  def __init__(self, i_seqs, angle_ideal):
    self.i_seqs = i_seqs
    self.angle_ideal = angle_ideal

def rice_rigidity(edge_lists, pdb_file_name, atom_attributes_list):
  print "number of atoms:", len(edge_lists)
  n_bonds = 0
  for i_seq,edge_list in enumerate(edge_lists):
    for j_seq in edge_list:
      if (i_seq > j_seq): continue
      assert i_seq != j_seq
      n_bonds += 1
  print "number of bonds:", n_bonds
  #
  have_cns_output = False
  if (pdb_file_name is not None):
    cns_out_file_name = pdb_file_name[:-3]+"out"
    if (os.path.isfile(cns_out_file_name)):
      have_cns_output = True
      cns_edge_lists = []
      for i_seq in xrange(len(edge_lists)):
        cns_edge_lists.append([])
      cns_centers_list = []
      cns_condih = []
      cns_ngp = None
      cns_groups = set()
      have_natom = False
      lines = iter(open(cns_out_file_name))
      for line in lines:
        if (line.startswith("TREE TOPOLOGY FOLLOWS:")):
          break
        flds = line.split()
        if (flds[:1] == ["NATOM"]):
          assert len(flds) == 2
          assert int(flds[1]) == len(edge_lists)
          have_natom = True
        elif (flds[:2] == ["ZZZ", "bond"]):
          assert len(flds) == 4
          i, j = [int(s) for s in flds[2:]]
          cns_edge_lists[i].append(j)
          cns_edge_lists[j].append(i)
        elif (flds[:3] == ["ZZZ", "WJ-1,", "WK-1"]):
          assert len(flds) == 5
          cns_centers_list.append(tuple(sorted([int(v) for v in flds[3:]])))
        elif (flds[:2] == ["ZZZ", "CONDIH"]):
          ndih = int(flds[2])
          assert len(flds) == 3 + ndih
          cns_condih.append([int(v) for v in flds[3:]])
        elif (flds[:2] == ["ZZZ", "NGP"]):
          assert len(flds) == 3
          cns_ngp = int(flds[2])
        elif (flds[:2] == ["ZZZ", "GROUP"]):
          assert len(flds) >= 3
          cns_groups.add(tuple(sorted([int(s) for s in flds[2:]])))
      assert have_natom
      assert len(cns_condih) == len(edge_lists)
      assert cns_ngp is not None
      cns_dof = None
      for line in lines:
        if (line.strip().startswith("TORMD3: number of degrees of freedom=")):
          cns_dof = int(line.split("=")[-1])
          break
      assert cns_dof is not None
      print "degrees of freedom ratio: %.6g" % (len(edge_lists)*3 / cns_dof)
      #
      aal = atom_attributes_list
      for i_seq,el,cns_el in zip(count(), edge_lists, cns_edge_lists):
        el = sorted(el)
        cns_el = sorted(cns_el)
        if (el != cns_el):
          print "bond list difference:"
          print i_seq, aal[i_seq].pdb_format()
          print " ", el, [aal[j_seq].pdb_format() for j_seq in el]
          print " ", cns_el, [aal[j_seq].pdb_format() for j_seq in cns_el]
          print
      if (1):
        edge_lists = cns_edge_lists
  #
  ijkls = set()
  for i_seq,edge_list in enumerate(edge_lists):
    for j_seq in edge_list:
      for k_seq in edge_lists[j_seq]:
        if (k_seq == i_seq): continue
        for l_seq in edge_lists[k_seq]:
          if (l_seq == j_seq): continue
          if (l_seq < i_seq): continue
          ijkl = (i_seq, j_seq, k_seq, l_seq)
          assert not ijkl in ijkls
          ijkls.add(ijkl)
  print "number of dihedrals:", len(ijkls)
  #
  jks = set()
  for d in ijkls:
    jks.add(tuple(sorted(d[1:3])))
  jks = sorted(jks)
  print "len(jks):", len(jks),
  if (have_cns_output):
    print "cns:", len(cns_centers_list),
    assert len(jks) == len(cns_centers_list)
  print
  if (0):
    for jk in jks:
      print " ", jk
  #
  if (have_cns_output):
    cns_jks = set()
    for cc in cns_centers_list:
      cns_jks.add(tuple(sorted(cc)))
    assert len(cns_jks) == len(jks)
    assert sorted(cns_jks) == jks
  #
  centers_list = []
  for i_seq in xrange(len(edge_lists)):
    centers_list.append(set())
  for j,k in jks:
    centers_list[j].add(k)
    centers_list[k].add(j)
  if (0):
    for i_seq,centers in enumerate(centers_list):
      print i_seq, sorted(centers)
      if (sorted(centers) != sorted(cns_condih[i_seq])):
        print " "*len(str(i_seq)), sorted(cns_condih[i_seq])
  #
  if (have_cns_output):
    counts = libtbx.dict_with_default_0()
    for i_seq,centers in enumerate(centers_list):
      for j_seq in centers:
        j_in_i = j_seq in cns_condih[i_seq]
        i_in_j = i_seq in cns_condih[j_seq]
        counts[(j_in_i, i_in_j)] += 1
    print "CONDIH counts:", counts
    assert counts.keys() == [(True,True)]
  #
  bonded_but_not_in_dihedral_center = []
  for i_seq in xrange(len(edge_lists)):
    bonded_but_not_in_dihedral_center.append([])
  for i_seq,edge_list in enumerate(edge_lists):
    for j_seq in edge_list:
      if (j_seq not in centers_list[i_seq]):
        bonded_but_not_in_dihedral_center[i_seq].append(j_seq)
  #
  is_assigned = [False] * len(edge_lists)
  rice_groups = []
  for i_seq_0 in xrange(len(edge_lists)):
    if (is_assigned[i_seq_0]): continue
    group = set()
    def traverse(i_seq):
      group.add(i_seq)
      is_assigned[i_seq] = True
      for j_seq in bonded_but_not_in_dihedral_center[i_seq]:
        if (is_assigned[j_seq]): continue
        traverse(i_seq=j_seq)
    traverse(i_seq=i_seq_0)
    rice_groups.append(tuple(sorted(group)))
  print "len(rice_groups):", len(rice_groups),
  if (have_cns_output):
    print "cns_ngp:", cns_ngp,
  print
  if (1):
    for group in rice_groups:
      print " ", list(group)
      if (have_cns_output):
        assert group in cns_groups
  if (have_cns_output):
    assert len(rice_groups) == len(cns_groups)
    return edge_lists
  return None

def compute_t_edge_counts(edge_lists):
  result = []
  for i_seq_0 in xrange(len(edge_lists)):
    t_edge_counts = [0,0,0,0]
    for i_seq_1 in edge_lists[i_seq_0]:
      for i_seq_2 in edge_lists[i_seq_1]:
        if (i_seq_2 == i_seq_0): continue
        have_link_02 = 0
        for i_seq_3 in edge_lists[i_seq_2]:
          if (i_seq_3 == i_seq_0):
            have_link_02 = 1
        for i_seq_3 in edge_lists[i_seq_2]:
          if (i_seq_3 == i_seq_0): continue
          if (i_seq_3 == i_seq_1): continue
          have_link_03 = 0
          have_link_13 = 0
          for i_seq_4 in edge_lists[i_seq_3]:
            if (i_seq_4 == i_seq_0): have_link_03 = 1
            if (i_seq_4 == i_seq_1): have_link_13 = 1
          t_edge_counts[3 - have_link_02 - have_link_03 - have_link_13] += 1
    result.append(t_edge_counts)
  return result

def complete_tetrahedra_cluster(edge_lists, cluster):
  queue = set()
  for i_seq in cluster:
    for j_seq in edge_lists[i_seq]:
      if (not j_seq in cluster):
        queue.add(j_seq)
  while (len(queue) != 0):
    next_queue = set()
    for i_seq in queue:
      connected = []
      not_connected = []
      for j_seq in edge_lists[i_seq]:
        if (j_seq in cluster):
          connected.append(j_seq)
        else:
          not_connected.append(j_seq)
      if (len(connected) > 2):
        connected.sort()
        cluster.add(i_seq)
        next_queue.update(not_connected)
      else:
        next_queue.add(i_seq)
    if (next_queue == queue): break
    queue = next_queue

def find_tetrahedra_clusters(edge_lists):
  clusters = set()
  for i_seq_0 in xrange(len(edge_lists)):
    for i_seq_1 in edge_lists[i_seq_0]:
      for i_seq_2 in edge_lists[i_seq_1]:
        if (i_seq_2 == i_seq_0): continue
        for i_seq_3 in edge_lists[i_seq_2]:
          if (i_seq_3 == i_seq_0):
            break
        else:
          continue
        for i_seq_3 in edge_lists[i_seq_2]:
          if (i_seq_3 == i_seq_0): continue
          if (i_seq_3 == i_seq_1): continue
          have_link_03 = False
          have_link_13 = False
          for i_seq_4 in edge_lists[i_seq_3]:
            if (i_seq_4 == i_seq_0): have_link_03 = True
            if (i_seq_4 == i_seq_1): have_link_13 = True
          if (have_link_03 and have_link_13):
            cluster = set([i_seq_0, i_seq_1, i_seq_2, i_seq_3])
            complete_tetrahedra_cluster(
              edge_lists=edge_lists,
              cluster=cluster)
            cluster = list(cluster)
            cluster.sort()
            clusters.add(tuple(cluster))
  return clusters

def join_clusters(clusters):
  # join all clusters with 3 or more common points
  lc = [set(c) for c in clusters]
  while True:
    def search():
      for ic in xrange(len(lc)-1):
        for jc in xrange(ic+1,len(lc)):
          common_points = lc[ic].intersection(lc[jc])
          if (len(common_points) >= 3):
            return (ic, jc)
      return None
    s = search()
    if (s is None):
      break
    ic, jc = s
    lc.append(lc[ic].union(lc[jc]))
    del lc[jc]
    del lc[ic]
  return lc

def cluster_construction(edge_list, edge_lists):
  clusters = find_tetrahedra_clusters(edge_lists=edge_lists)
  print "tetrahedra_clusters:", len(clusters), clusters
  joined_clusters = join_clusters(clusters=clusters)
  print "joined clusters:", len(joined_clusters), joined_clusters
  #
  # verify that joined_clusters really are rigid
  for cluster in joined_clusters:
    reindexing_table = {}
    for i in cluster:
      reindexing_table[i] = len(reindexing_table)
    assert len(reindexing_table) == len(cluster)
    cluster_edge_list = []
    for e in edge_list:
      e = [reindexing_table.get(i, -1) for i in e]
      e.sort()
      if (e[0] == -1): continue
      cluster_edge_list.append(tuple(e))
    cluster_dof = determine_degrees_of_freedom(
      n_dim=3, n_vertices=len(cluster), edge_list=cluster_edge_list)
    assert cluster_dof == 6

def commutative_pair_iterator(elements):
  n = len(elements)
  for i in xrange(n-1):
    for j in xrange(i+1,n):
      yield (elements[i], elements[j])

def find_triangles(edge_lists, i_seq_0):
  for i_seq_1,i_seq_2 in commutative_pair_iterator(edge_lists[i_seq_0]):
    if (i_seq_2 in edge_lists[i_seq_1]):
      yield (i_seq_1, i_seq_2)

def find_best_tetrahedron(edge_lists, i_seq_0):
  # find all triangles including i_seq_0
  # for each triangle: find additional node with most connections to triangle
  # if no triangles:
  #   does any of the connected vertices have triangles?
  #     yes: take any and attach i_seq_0 as a rod
  #     no:
  #       does i_seq_0 have three connections?
  #       yes: take these (any) three connections
  #       no: find any chain of four nodes
  best_triangle = None
  best_n = 0
  best_i_seq_3 = None
  best_have_i3 = None
  for i_seq_1,i_seq_2 in find_triangles(edge_lists=edge_lists,i_seq_0=i_seq_0):
    triangle = [i_seq_0,i_seq_1,i_seq_2]
    for ii0 in [0,1,2]:
      ii1 = (ii0 + 1) % 3
      ii2 = (ii1 + 1) % 3
      for i_seq_3 in edge_lists[triangle[ii0]]:
        if (i_seq_3 in triangle): continue
        n = 1
        have_i3 = [False,False,False]
        have_i3[ii0] = True
        for iii in [ii1, ii2]:
          if (triangle[iii] in edge_lists[i_seq_3]):
            have_i3[iii] = True
            n += 1
        if (best_n < n):
          best_triangle = triangle
          best_n = n
          best_i_seq_3 = i_seq_3
          best_have_i3 = have_i3
  def e(i,j):
    i_seq, j_seq = result[i], result[j]
    if (i_seq < j_seq): return (i_seq,j_seq)
    return (j_seq,i_seq)
  if (best_triangle is not None):
    result = best_triangle + [best_i_seq_3]
    fixed_edges = set([e(0,1), e(1,2), e(2,0)])
    free_edges = set()
    for i,f in enumerate(best_have_i3):
      if (f): fixed_edges.add(e(i,3))
      else: free_edges.add(e(i,3))
    return result, fixed_edges, free_edges
  #
  for i_seq_1 in edge_lists[i_seq_0]:
    for i_seq_2,i_seq_3 in find_triangles(
                             edge_lists=edge_lists, i_seq_0=i_seq_1):
      result = [i_seq_0, i_seq_1, i_seq_2, i_seq_3]
      if (len(set(result)) == 4):
        fixed_edges = set([e(0,1), e(1,2), e(2,3), e(3,1)])
        free_edges = set([e(0,2), e(0,3)])
        return result, fixed_edges, free_edges
  #
  if (len(edge_lists[i_seq_0]) >= 3):
    result = [i_seq_0] + edge_lists[i_seq_0][:3]
    fixed_edges = set([e(0,1), e(0,2), e(0,3)])
    free_edges = set([e(1,2), e(1,3), e(2,3)])
    return result, fixed_edges, free_edges
  #
  if (len(edge_lists[i_seq_0]) > 0):
    result = [i_seq_0] + edge_lists[i_seq_0]
    ii = 1
    def add():
      if (ii == len(result)): return False
      for i in edge_lists[result[ii]]:
        if (i not in result):
          result.append(i)
          if (len(result) == 4):
            return False
      return True
    while (add()): ii += 1
    if (len(result) == 4):
      fixed_edges = set()
      free_edges = set()
      for i_seq,j_seq in commutative_pair_iterator(result):
        e = tuple(sorted([i_seq,j_seq]))
        if (j_seq in edge_lists[i_seq]):
          fixed_edges.add(e)
        else:
          free_edges.add(e)
      assert len(fixed_edges) >= 3
      assert len(fixed_edges) + len(free_edges) == 6
      return result, fixed_edges, free_edges
  #
  return None, None, None

def find_best_next_point(edge_lists, points_placed_set):
  best_i_seq = None
  best_attached_to = []
  for i_seq_0 in points_placed_set:
    for i_seq_1 in edge_lists[i_seq_0]:
      if (i_seq_1 in points_placed_set): continue
      attached_to = []
      for i_seq_2 in edge_lists[i_seq_1]:
        if (i_seq_2 in points_placed_set):
          attached_to.append(i_seq_2)
      if (len(attached_to) > len(best_attached_to)):
        best_i_seq = i_seq_1
        best_attached_to = attached_to
  return best_i_seq, best_attached_to

def construct_first_tetrahedron_vertices(
      distances,
      points_placed,
      fixed_edges,
      free_edges):
  print "fixed:", fixed_edges
  print "free:", free_edges
  assert len(fixed_edges) >= 3
  assert len(fixed_edges) + len(free_edges) == 6
  result = [None] * len(distances)
  def get_distance(i,j):
    i_seq = points_placed[i]
    j_seq = points_placed[j]
    if (i_seq > j_seq): i_seq, j_seq = j_seq, i_seq
    return distances[i_seq][j_seq]
  if (len(fixed_edges) == 3):
    assert 0
  elif (len(fixed_edges) == 4):
    assert 0
  elif (len(fixed_edges) == 5):
    assert 0
  else:
    root = cg3d.root_node(site=matrix.col((0,0,0)))
    root.connections.append(
      cg3d.chain_node(
        serial=1,
        distance=get_distance(0,1),
        angles=[0, 0]))
    root.connections[0].connections.append(
      cg3d.loop_node(
        serial=2,
        distance=get_distance(1,2),
        angle=0,
        closing_distance=get_distance(0,2),
        closing_serial=0))
    tripod = tripod_node(
      points=root.compute_node_sites(),
      distances=[get_distance(i,3) for i in xrange(3)],
      p3_sign=1)
    for i,vertex in zip(points_placed, tripod.compute_nodes()):
      result[i] = vertex
  return result

def attach_to_already_placed_vertices(
      distances,
      vertices_placed,
      next_i_seq,
      next_attached_to):
  def get_distance(i_seq, j_seq):
    if (i_seq > j_seq): i_seq, j_seq = j_seq, i_seq
    return distances[i_seq][j_seq]
  if (len(next_attached_to) >= 3):
    nat = next_attached_to[:3]
    points = [vertices_placed[i_seq] for i_seq in nat]
    if (None in points):
      print "FAILURE attach_to_already_placed_vertices()"
      return
    p3s = []
    for p3_sign in [1,-1]:
      p3s.append(tripod_node(
        points=points,
        distances=[get_distance(i_seq, next_i_seq) for i_seq in nat],
        p3_sign=p3_sign).p3)
    min_ds = []
    for p3 in p3s:
      if (p3 is None):
        min_d = 0
      else:
        min_d = None
        for v in  vertices_placed:
          if (v is None): continue
          d = abs(v - p3)
          if (min_d is None or min_d > d):
            min_d = d
      min_ds.append(min_d)
    print min_ds
    vertices_placed[next_i_seq] = p3s[int(min_ds[0] < min_ds[1])]
  else:
    assert 0

class t_roots(object):

  def __init__(self, i_seqs, fixed_edges, free_edges):
    self.i_seqs = list(i_seqs)
    self.fixed_edges = fixed_edges
    self.free_edges = free_edges

class t_placement(object):

  def __init__(self, i_seq, attached_to):
    self.i_seq = i_seq
    self.attached_to = attached_to

class t_const_params(object):

  def __init__(self, i_seq, attached_to, params, fixed=False):
    self.i_seq = i_seq
    self.attached_to = attached_to
    self.params = params
    self.fixed = fixed

class t_const_dep_info(object):

  def __init__(self, i_seq):
    self.i_seq = i_seq
    self.data = []

  def merge(self, other):
    self.data.append(other.data)

def build_from_t_const_params(params, n_sites=None):
  if (n_sites is None): n_sites = len(params)
  result = [None] * n_sites
  for p in params:
    if (p.attached_to is None):
      result[p.i_seq] = matrix.col(p.params)
    elif (len(p.attached_to) >= 3):
      result[p.i_seq] = p.params.site(
        base_sites=[result[i_seq] for i_seq in p.attached_to[:3]])
    elif (len(p.attached_to) == 2):
      result[p.i_seq] = p.params.site(
        base_sites=[result[i_seq] for i_seq in p.attached_to])
    else:
      result[p.i_seq] = p.params.site(
        base_site=result[p.attached_to[0]])
  return result

def inspect_t_const_params(edge_lists, params):
  problem_edges = []
  for p in params:
    if (p.attached_to is None): continue
    if (len(p.attached_to) <= 3): continue
    for j_seq in p.attached_to[3:]:
      problem_edges.append(tuple(sorted([p.i_seq, j_seq])))
  print "problem_edges:", problem_edges
  #
  fixed_edges = []
  pe_set = set(problem_edges)
  for i_seq,edge_list in enumerate(edge_lists):
    for j_seq in edge_list:
      if (j_seq < i_seq): continue
      e = (i_seq, j_seq)
      if (e in problem_edges): continue
      fixed_edges.append(e)
  del pe_set
  #
  def compute_distances():
    sites = build_from_t_const_params(params=params)
    problem_distances = []
    for i,j in problem_edges:
      problem_distances.append(abs(sites[i]-sites[j]))
    fixed_distances = []
    for i,j in fixed_edges:
      fixed_distances.append(abs(sites[i]-sites[j]))
    return problem_distances, fixed_distances
  problem_distances, fixed_distances = compute_distances()
  #
  variable_flags = [False] * len(problem_distances)
  n_variables = []
  for p in params:
    fixed = p.fixed
    if (isinstance(fixed, str)): # XXX
      print "WARNING:", fixed
      fixed = False
    if (fixed): continue
    if (p.attached_to is None): continue
    if (isinstance(p.params, nodes_3d.point)): continue
    def eval_distances():
      n_variable = 0
      for ie,e,pd,pde in zip(count(),problem_edges,problem_distances,pd_eps):
        if (abs(pde-pd) > 1.e-10):
          print "circle param %d changes %s: %.4g - %.4g = %.4g" % (
            p.i_seq, str(e), pde, pd, pde-pd)
          variable_flags[ie] = True
          n_variable += 1
        else:
          print "circle param %d invariant %s: %.4g" % (
            p.i_seq, str(e), pde-pd)
      return n_variable
    if (isinstance(p.params, nodes_3d.circle)):
      angle_eps = degrees_as_rad(0.15)
      angle_orig = p.params.angle
      p.params.angle = angle_orig + angle_eps
      try:
        pd_eps, fd_eps = compute_distances()
      except (TypeError, AttributeError):
        p.params.angle = angle_orig - angle_eps
        pd_eps, fd_eps = compute_distances()
      p.params.angle = angle_orig
      assert approx_equal(fd_eps, fixed_distances, eps=1.e-12)
      n_variables.append(eval_distances())
    elif (isinstance(p.params, nodes_3d.sphere)):
      angle_eps = degrees_as_rad(0.2)
      nv = []
      for i_angle in [0,1]:
        angle_orig = p.params.angles[i_angle]
        p.params.angles[i_angle] = angle_orig + angle_eps
        try:
          pd_eps, fd_eps = compute_distances()
        except (TypeError, AttributeError, AssertionError):
          p.params.angles[i_angle] = angle_orig - angle_eps
          pd_eps, fd_eps = compute_distances()
        p.params.angles[i_angle] = angle_orig
        assert approx_equal(fd_eps, fixed_distances, eps=1.e-12)
        nv.append(eval_distances())
      n_variables.append(nv)
    else:
      raise RuntimeError
  for n in n_variables:
    if (n != 0 and n != [0,0]):
      print "n_variables:", n_variables
      break
  invariant_edges = []
  for e,f in zip(problem_edges,variable_flags):
    if (not f): invariant_edges.append(e)
  if (len(invariant_edges) != 0):
    print "invariant edges:", invariant_edges
  #
  # for each constructed point, keep track with degrees of freedom
  #   - it depends on
  #   - are neutral (two points defining hinge)
  dependency_sets = {}
  neutral_sets = {}
  for p in params:
    fixed = p.fixed
    if (isinstance(fixed, str)): # XXX
      print "WARNING:", fixed
      fixed = False
    dep_set = set()
    introduces_var = not fixed and not isinstance(p.params, nodes_3d.point)
    if (introduces_var):
      dep_set.add(p.i_seq)
    if (p.attached_to is not None):
      for j_seq in p.attached_to:
        dep_set.update(dependency_sets[j_seq])
      if (introduces_var and len(p.attached_to) == 2):
        for j_seq in p.attached_to:
          neutral_sets.setdefault(j_seq, set()).add(p.i_seq)
    dependency_sets[p.i_seq] = dep_set
    print "t_const: %2d" % p.i_seq, p.attached_to, \
      "dep set:", sorted(dependency_sets[p.i_seq])
  print "neutral_sets:", neutral_sets
  #
  i_placed = [None] * len(params)
  for i,p in enumerate(params):
    i_placed[p.i_seq] = i
  #
  for e in problem_edges:
    i,j = e
    ai = params[i_placed[i]].attached_to
    aj = params[i_placed[j]].attached_to
    print "LOOK", e, dependency_sets[i], dependency_sets[j], neutral_sets.get(i), neutral_sets.get(j), ai, aj, {True: "ISRED", False: "NONRED"}[e in invariant_edges]
  #
  return problem_edges, invariant_edges

class t_construction(object):

  def __init__(self,
        edge_lists,
        distances=None,
        fixed_root_i_seq=None,
        sites=None):
    assert distances is None or len(edge_lists) == len(distances)
    self.n_vertices = len(edge_lists)
    self.i_placed = [None] * self.n_vertices
    self.n_dof = None
    self.p_dof = None
    self.hinges = []
    if (0):
      self.fixed_downstream = libtbx.dict_with_default_0()
    else:
      self.fixed_downstream = None
    list_of_t_edge_counts = compute_t_edge_counts(edge_lists=edge_lists)
    #
    if (fixed_root_i_seq is not None):
      root_i_seq = fixed_root_i_seq
      print "fixed root:", root_i_seq
    else:
      root_i_seq = 0
      root_t_edge_counts = list_of_t_edge_counts[0]
      for i_seq,t_edge_counts in enumerate(list_of_t_edge_counts):
        def cmp_t_edge_counts(a, b):
          for ai,bi in zip(a,b):
            c = cmp(ai,bi)
            if (c != 0): return -c
          return 0
        if (cmp_t_edge_counts(t_edge_counts, root_t_edge_counts) < 0):
          root_i_seq = i_seq
          root_t_edge_counts = t_edge_counts
      print "root:", root_i_seq, root_t_edge_counts
    #
    self.points_placed, fixed_edges, free_edges = find_best_tetrahedron(
      edge_lists=edge_lists, i_seq_0=root_i_seq)
    if (self.points_placed is None):
      print "t_construction not implemented."
      return
    self.points_placed.sort()
    print "root_points:", self.points_placed, fixed_edges, free_edges
    if (0 and distances is not None and len(self.points_placed) == 4):
      vertices_placed = construct_first_tetrahedron_vertices(
        distances=distances,
        points_placed=self.points_placed,
        fixed_edges=fixed_edges,
        free_edges=free_edges)
    else:
      vertices_placed = None
    self.roots = t_roots(
      i_seqs=self.points_placed,
      fixed_edges=fixed_edges,
      free_edges=free_edges)
    for i_seq in self.roots.i_seqs:
      self.i_placed[i_seq] = -1
    self.placements = []
    if (sites is None):
      params = []
    else:
      params = self.parameterize_root_tetrahedron(sites=sites)
    n_dof = len(free_edges)
    p_dof = 0
    print "  dof:", n_dof, p_dof
    points_placed_set = set(self.points_placed)
    if (n_dof == 1):
      self.hinges.append(tuple(sorted(
        set(self.points_placed).difference(set(list(free_edges)[0])))))
    while True:
      next_i_seq, next_attached_to = find_best_next_point(
        edge_lists=edge_lists,
        points_placed_set=points_placed_set)
      if (next_i_seq is None):
        break
      self.i_placed[next_i_seq] = len(self.placements)
      def cmp_atto(a, b):
        result = cmp(self.i_placed[a], self.i_placed[b])
        if (result != 0): return result
        return cmp(a, b)
      next_attached_to = sorted(next_attached_to, cmp_atto)
      if (len(next_attached_to) > 3):
        self.probe_dofs(i_seq=next_i_seq, attached_to=next_attached_to)
      self.placements.append(
        t_placement(i_seq=next_i_seq, attached_to=next_attached_to))
      if (1):
        print "next: %3d %3d" % (3-len(next_attached_to), next_i_seq), \
          next_attached_to
      if (len(next_attached_to) == 2):
        self.hinges.append(tuple(sorted(next_attached_to)))
      if (vertices_placed is not None):
        attach_to_already_placed_vertices(
          distances=distances,
          vertices_placed=vertices_placed,
          next_i_seq=next_i_seq,
          next_attached_to=next_attached_to)
      if (len(params) != 0):
        if (len(next_attached_to) >= 3):
          n = nodes_3d.point.from_sites(
            base_sites=[sites[i_seq] for i_seq in next_attached_to[:3]],
            site=sites[next_i_seq])
        elif (len(next_attached_to) == 2):
          n = nodes_3d.circle.from_sites(
            base_sites=[sites[i_seq] for i_seq in next_attached_to],
            site=sites[next_i_seq])
        else:
          n = nodes_3d.sphere.from_sites(
            base_site=sites[next_attached_to[0]],
            site=sites[next_i_seq])
        params.append(t_const_params(
          i_seq=next_i_seq,
          attached_to=next_attached_to,
          params=n))
      n_dof += 3 - min(3, len(next_attached_to))
      p_dof += max(0, len(next_attached_to)-3)
      if (0):
        print "  dof:", n_dof, p_dof
      self.points_placed.append(next_i_seq)
      points_placed_set.add(next_i_seq)
    print "final dof:", n_dof, p_dof
    print "number of hinges:", len(self.hinges)
    if (1):
      print "hinges:", self.hinges
    if (vertices_placed is not None):
      print "vertices_placed:"
      for v in vertices_placed:
        if (v is None):
          print v
        else:
          print "(%.6g,%.6g,%.6g)" % tuple(v)
      if (not None in vertices_placed):
        for i_seq,edge_list in enumerate(edge_lists):
          for j_seq in edge_list:
            if (i_seq > j_seq): continue
            d = abs(vertices_placed[i_seq] - vertices_placed[j_seq])
            # XXX assert approx_equal(d, distances[i_seq][j_seq])
    print "points_placed:", self.points_placed
    print "i_placed:", self.i_placed
    print "fixed_downstream:", self.fixed_downstream
    self.n_dof = n_dof
    self.p_dof = p_dof
    if (sites is not None):
      assert len(params) == len(sites)
      sites_reconstructed = build_from_t_const_params(params=params)
      assert approx_equal(
        [tuple(s) for s in sites_reconstructed],
        [tuple(s) for s in sites])
      self.problem_edges, self.invariant_edges = inspect_t_const_params(
        edge_lists=edge_lists, params=params)
      if (self.n_dof == 0):
        assert self.invariant_edges == self.problem_edges
      if (self.p_dof == 0):
        assert len(self.invariant_edges) == 0

  def probe_dofs(self, i_seq, attached_to):
    if (self.fixed_downstream is None):
      return
    print "probe_dofs start"
    for j_seq in attached_to:
      print "  Can change distance?", i_seq, j_seq
      if (j_seq in self.roots.i_seqs):
        for edge in self.roots.free_edges:
          print "    dof root free edge", edge
          if (j_seq in edge):
            print "        YES"
            self.fixed_downstream[edge] = 1
      for placement in self.placements:
        if (len(placement.attached_to) > 2): continue
        print "    dof", placement.i_seq, placement.attached_to
        ip = self.i_placed[placement.i_seq]
        cand = set(self.points_placed[:len(self.roots.i_seqs)+ip]) \
             - set(placement.attached_to)
        print "      candidates:", cand
        if (j_seq in cand):
          print "        YES"
          if (self.fixed_downstream[ip] < 3-len(placement.attached_to)):
            self.fixed_downstream[ip] += 1

  def parameterize_root_tetrahedron(self, sites):
    assert len(self.roots.i_seqs) == 4
    nrfe = len(self.roots.free_edges)
    assert nrfe in [0,1,2,3]
    result = []
    def connectivity_info():
      cc = libtbx.dict_with_default_0()
      for e in self.roots.fixed_edges:
        for i in e:
          cc[i] += 1
      result = {}
      for i,n in cc.items():
        result.setdefault(n, []).append(i)
      return result
    if (nrfe == 0):
      # internal and global dofs not separated:
      #   pick one point as root node
      #   pick one point to become sphere node
      #   pick one point to become cirle node (3-loop)
      #   pick last point to become point node
      #     dofs: 3 + 2 + 1 + 0 = 6
      # separated:
      #   simply place tetrahedron where it is
      #     dofs: 0
      ri = self.roots.i_seqs
      result.append(t_const_params(
        i_seq=ri[0],
        attached_to=None,
        params=sites[ri[0]],
        fixed=True))
      result.append(t_const_params(
        i_seq=ri[1],
        attached_to=[ri[0]],
        params=nodes_3d.sphere.from_sites(
          base_site=sites[ri[0]], site=sites[ri[1]]),
        fixed=True))
      result.append(t_const_params(
        i_seq=ri[2],
        attached_to=ri[:2],
        params=nodes_3d.circle.from_sites(
          base_sites=[sites[ri[0]], sites[ri[1]]], site=sites[ri[2]]),
        fixed=True))
      result.append(t_const_params(
        i_seq=ri[3],
        attached_to=ri[:3],
        params=nodes_3d.point.from_sites(
          base_sites=[sites[ri[0]], sites[ri[1]], sites[ri[2]]],
          site=sites[ri[3]]),
        fixed=True))
    elif (nrfe == 1):
      # internal and global dofs not separated:
      #   pick one of the hinge points as fixed root node
      #   pick the second hinge point as fixed sphere node
      #   pick one point as fixed cirle node (3-loop)
      #   pick last point as cirle node (3-loop)
      #     dofs: 3 + 2 + 1 + 1 = 7
      # separated:
      #   put one triangle where it is
      #   determine hinge angle to place fourth point
      #     dofs: 0 + 1
      fe = sorted(iter(self.roots.free_edges).next())
      hinge = []
      for i_seq in self.roots.i_seqs:
        if (i_seq in fe): continue
        hinge.append(i_seq)
      hinge.sort()
      result.append(t_const_params(
        i_seq=hinge[0],
        attached_to=None,
        params=sites[hinge[0]],
        fixed=True))
      result.append(t_const_params(
        i_seq=hinge[1],
        attached_to=[hinge[0]],
        params=nodes_3d.sphere.from_sites(
          base_site=sites[hinge[0]], site=sites[hinge[1]]),
        fixed=True))
      for i_seq in fe:
        result.append(t_const_params(
          i_seq=i_seq,
          attached_to=hinge,
          params=nodes_3d.circle.from_sites(
            base_sites=[sites[hinge[0]], sites[hinge[1]]], site=sites[i_seq]),
          fixed=len(result)==2))
    elif (nrfe == 2):
      # 1. triangle with attached rod
      #   internal and global dofs not separated:
      #     pick the node with three connections as the root node
      #     pick a node in the triangle as a sphere node
      #     pick the last node in the triangle as a circle node (3-loop)
      #     pick the last point as a sphere node
      #       dofs: 3 + 2 + 1 + 2 = 8
      #   separated:
      #     put triangle where it is
      #     add last point as sphere node
      #       dofs: 0 + 2
      # 2. 4-loop
      #   internal and global dofs not separated:
      #     pick one node as the root node
      #     pick connected node as sphere node
      #     pick connected node as sphere node
      #     pick connected node as circle node (4-loop)
      #       dofs: 3 + 2 + 2 + 1 = 8
      #   separated:
      #     pick one node as the fixed root node
      #     pick connected node as fixed sphere node
      #     pick connected node as plane-circle node
      #     pick connected node as circle node
      #       dofs: 0 + 0 + 1 + 1
      ci = connectivity_info()
      assert sorted(ci.keys()) in [[2], [1,2,3]]
      if (len(ci) == 3): # triangle with attached rod
        result.append(t_const_params(
          i_seq=ci[3][0],
          attached_to=None,
          params=sites[ci[3][0]],
          fixed=True))
        result.append(t_const_params(
          i_seq=ci[2][0],
          attached_to=[ci[3][0]],
          params=nodes_3d.sphere.from_sites(
            base_site=sites[ci[3][0]], site=sites[ci[2][0]]),
          fixed=True))
        result.append(t_const_params(
          i_seq=ci[2][1],
          attached_to=[ci[3][0], ci[2][0]],
          params=nodes_3d.circle.from_sites(
            base_sites=[sites[ci[3][0]], sites[ci[2][0]]],
            site=sites[ci[2][1]]),
          fixed=True))
        result.append(t_const_params(
          i_seq=ci[1][0],
          attached_to=[ci[3][0]],
          params=nodes_3d.sphere.from_sites(
            base_site=sites[ci[3][0]], site=sites[ci[1][0]])))
      else: # 4-loop
        i0 = min(self.roots.i_seqs)
        result.append(t_const_params(
          i_seq=i0,
          attached_to=None,
          params=sites[i0],
          fixed=True))
        next = []
        for i,j in self.roots.fixed_edges:
          if   (i == i0): next.append(j)
          elif (j == i0): next.append(i)
        i1 = min(next)
        result.append(t_const_params(
          i_seq=i1,
          attached_to=[i0],
          params=nodes_3d.sphere.from_sites(
            base_site=sites[i0], site=sites[i1]),
          fixed=True))
        def search_next(ip, ic):
          for i,j in self.roots.fixed_edges:
            if (i == ic):
              if (j != ip):
                return j
            elif (j == ic):
              if (i != ip):
                return i
        i2 = search_next(i0, i1)
        result.append(t_const_params(
          i_seq=i2,
          attached_to=[i1],
          params=nodes_3d.sphere.from_sites(
            base_site=sites[i1], site=sites[i2]),
          fixed="PLANE_NOT_IMPLEMENTED"))
        i3 = search_next(i1, i2)
        result.append(t_const_params(
          i_seq=i3,
          attached_to=[i0, i2],
          params=nodes_3d.circle.from_sites(
            base_sites=[sites[i0], sites[i2]],
            site=sites[i3])))
    else:
      # 1. chain of three rods
      #   internal and global dofs not separated:
      #     pick one end-node as the root node
      #     pick connected node as sphere node
      #     pick connected node as sphere node
      #     pick connected node as sphere node
      #       dofs: 3 + 2 + 2 + 2 = 9
      #   separated:
      #     pick one node as fixed root node
      #     pick connected node as fixed sphere node
      #     pick connected node as plane-circle node
      #     pick connected node as sphere node
      #       dofs: 0 + 0 + 1 + 2
      # 2. three rods connected in one point
      #   internal and global dofs not separated:
      #     pick central node as the root node
      #     pick connected node as sphere node
      #     pick connected node as sphere node
      #     pick connected node as sphere node
      #       dofs: 3 + 2 + 2 + 2 = 9
      #   separated:
      #     pick central node as fixed root node
      #     pick connected node as fixed sphere node
      #     pick connected node as plane-circle node
      #     pick connected node as sphere node
      #       dofs: 0 + 0 + 1 + 2
      ci = connectivity_info()
      assert sorted(ci.keys()) in [[1,2], [1,3]]
      if (2 in ci): # chain of three rods
        i0, i3 = sorted(ci[1])
        i1, i2 = None, None
        for i,j in self.roots.fixed_edges:
          if   (i == i0): i1 = j
          elif (j == i0): i1 = i
          if   (i == i3): i2 = j
          elif (j == i3): i2 = i
        assert i1 is not None
        assert i2 is not None
        pairs = [(i0,i1,True),(i1,i2,"PLANE_NOT_IMPLEMENTED"),(i2,i3,False)]
      else: # three rods connected in one point
        i0 = ci[3][0]
        i1, i2, i3 = sorted(ci[1])
        pairs = [(i0,i1,True),(i0,i2,"PLANE_NOT_IMPLEMENTED"),(i0,i3,False)]
      assert sorted([i0, i1, i2, i3]) == sorted(self.roots.i_seqs)
      result.append(t_const_params(
        i_seq=i0,
        attached_to=None,
        params=sites[i0],
        fixed=True))
      for i,j,fixed in pairs:
        result.append(t_const_params(
          i_seq=j,
          attached_to=[i],
          params=nodes_3d.sphere.from_sites(
            base_site=sites[i], site=sites[j]),
          fixed=fixed))
    sites_reconstructed = build_from_t_const_params(
      params=result, n_sites=len(sites))
    assert approx_equal(
      [tuple(sites_reconstructed[i_seq]) for i_seq in self.roots.i_seqs],
      [tuple(sites[i_seq]) for i_seq in self.roots.i_seqs])
    return result

def tetrahedra_hunt(edge_lists):
  print "len(edge_lists):", len(edge_lists)
  tverts_list_per_vertex = [set() for i_seq in xrange(len(edge_lists))]
  flags = [False] * len(edge_lists)
  for i_seq_pivot in xrange(len(edge_lists)):
    shell = set()
    def traverse(i_seq, depth):
      depth += 1
      shell.add(i_seq)
      if (depth < 4):
        flags[i_seq] = True
        for j_seq in edge_lists[i_seq]:
          if (flags[j_seq]): continue
          traverse(i_seq=j_seq, depth=depth)
    traverse(i_seq=i_seq_pivot, depth=0)
    for i_seq in shell:
      flags[i_seq] = False
    if (len(shell) <= 4):
      # dirty: keep track of incomplete tetrahedra, to be removed below
      tverts_list_per_vertex[i_seq_pivot].add(tuple(sorted(shell)))
    else:
      shell.remove(i_seq_pivot)
      shell = list(shell)
      for i in xrange(len(shell)-2):
        i_seq = shell[i]
        for j in xrange(i+1,len(shell)-1):
          j_seq = shell[j]
          for k in xrange(j+1,len(shell)):
            k_seq = shell[k]
            tverts_list_per_vertex[i_seq_pivot].add(tuple(sorted(
              [i_seq_pivot,i_seq,j_seq,k_seq])))
  #
  potential_implicit_edges = set()
  for tverts_list in tverts_list_per_vertex:
    for tverts in list(tverts_list):
      n = len(tverts)
      for i in xrange(n-1):
        i_seq = tverts[i]
        for j in xrange(i+1,n):
          j_seq = tverts[j]
          if (not j_seq in edge_lists[i_seq]):
            potential_implicit_edges.add((i_seq,j_seq))
      if (n != 4):
        # dirty: remove incomplete tetrahedra here (see above)
        tverts_list.remove(tverts)
  if (0):
    for e in potential_implicit_edges:
      print "pie:", e
  print "len(potential_implicit_edges):", len(potential_implicit_edges)
  #
  if (0):
    # experiment with all 3-cycles of given and implied tetrahedra
    edge_indices = {}
    for i_seq,edge_list in enumerate(edge_lists):
      for j_seq in edge_list:
        if (i_seq > j_seq): continue
        assert i_seq != j_seq
        edge_indices[(i_seq,j_seq)] = len(edge_indices)
    n_edges = len(edge_indices)
    for e in potential_implicit_edges:
      assert e[0] < e[1]
      edge_indices[e] = len(edge_indices)
    n_xedges = len(edge_indices)
    assert n_xedges == n_edges + len(potential_implicit_edges)
    #
    matrix = []
    for triangle in triangle_set(tverts_list_per_vertex):
      assert len(triangle) == 3
      row = [0] * n_xedges
      for i,j in [(0,1),(0,2),(1,2)]:
        i = edge_indices[(triangle[i],triangle[j])]
        row[i] = 1
      matrix.append(row)
      if (0):
        print "o:", row[:n_edges], row[n_edges:]
    if (len(matrix) != 0):
      free_vars, row_perm = mod2_row_echelon_form(m=matrix)
      if (0):
        for row in matrix:
          print "r:", row[:n_edges], row[n_edges:]
      n = 0
      for ic in free_vars:
        if (ic < n_edges): n += 1
      # conclusion?
      print "LOOK:", len(free_vars), n_xedges-len(free_vars), n, n_edges-n
  #
  return tverts_list_per_vertex, potential_implicit_edges

def triangle_set(tverts_list_per_vertex):
  result = set()
  for tverts_list in tverts_list_per_vertex:
    for tverts in tverts_list:
      assert len(tverts) == 4
      for i in xrange(4):
        result.add(tverts[:i] + tverts[i+1:])
  return result

def old_find_face_sharing_tetrahedra(tverts_list_per_vertex):
  n_seq = len(tverts_list_per_vertex)
  for i_seq in xrange(n_seq):
    shell_i = set()
    for tverts_i in tverts_list_per_vertex[i_seq]:
      shell_i.update(tverts_i)
    sharing = {1: set(), 2: set(), 3: set()}
    for j_seq in shell_i:
      for tverts_i in tverts_list_per_vertex[i_seq]:
        ti = set(tverts_i)
        for tverts_j in tverts_list_per_vertex[j_seq]:
          tj = set(tverts_j)
          tij = ti.intersection(tj)
          n = len(tij)
          if (n in [0,4]): continue
          sharing[n].add(tuple(sorted(tij)))
    for n in [1,2,3]:
      for common in sharing[n]:
        print common

def face_sharing_edge_counts(edge_lists, ti, tj, tij):
  base = list(tij)
  pi = list(ti - tij)[0]
  pj = list(tj - tij)[0]
  nb = 0
  for i_seq,j_seq in commutative_pair_iterator(base):
    if (j_seq in edge_lists[i_seq]): nb += 1
  ni = 0
  for j_seq in base:
    if (j_seq in edge_lists[pi]): ni += 1
  nj = 0
  for j_seq in base:
    if (j_seq in edge_lists[pj]): nj += 1
  return nb, ni, nj

def find_face_sharing_tetrahedra(edge_lists, tverts_list_per_vertex):
  # UNFINISHED EXPERIMENT
  all_tverts = set()
  n_seq = len(tverts_list_per_vertex)
  for i_seq in xrange(n_seq):
    for tverts in tverts_list_per_vertex[i_seq]:
      all_tverts.add(tverts)
  # find combinations of face-sharing tetrahedra with enough edges to
  # make each combination rigid
  # for sure: each shared face makes one edge redundant
  # simply list all face-sharing pairs of tetrahedra, together with
  # the numbers fixed and free edges
  all_tverts = sorted(all_tverts)
  face_sharing_counts = libtbx.dict_with_default_0()
  for i in xrange(len(all_tverts)-1):
    ti = set(all_tverts[i])
    for j in xrange(i+1,len(all_tverts)):
      tj = set(all_tverts[j])
      tij = ti.intersection(tj)
      if (len(tij) != 3): continue
      nb, ni, nj = face_sharing_edge_counts(
        edge_lists=edge_lists, ti=ti, tj=tj, tij=tij)
      if (nb < 2 or ni < 2 or nj < 2): continue
      print "shared face:", all_tverts[i], all_tverts[j], nb, ni, nj
      face_sharing_counts[tuple(sorted(tij))] += 1
  print "FFST-COUNTS:", face_sharing_counts

class cycle_enumeration(object):

  def __init__(self, n_vertices, bond_lists):
    # J. D. Horton, SIAM J. Comput. Vol. 16, No. 2, April 1987
    # A polynomial-time algorithm to find the shortest cycle basis of a graph
    #
    # (1) Find a minimum path P(x, y) between each pair of vertices x, y.
    shortest_paths = []
    for i in xrange(n_vertices):
      shortest_paths.append([None]*n_vertices)
    for i_seq_root in xrange(n_vertices):
      traversed = [False]*n_vertices
      path = []
      def traverse(i_seq):
        traversed[i_seq] = True
        path.append(i_seq)
        for bond in bond_lists[i_seq]:
          j_seq = bond.j_seq
          if (j_seq == i_seq_root): continue
          if (shortest_paths[i_seq_root][j_seq] is None):
            shortest_paths[i_seq_root][j_seq] = \
            shortest_paths[j_seq][i_seq_root] = path + [j_seq]
        for bond in bond_lists[i_seq]:
          j_seq = bond.j_seq
          if (not traversed[j_seq]):
            traverse(i_seq=j_seq)
        path.pop()
      traverse(i_seq=i_seq_root)
    #
    # (2) For each vertex v and edge {x, y} in the graph, create the cycle
    #     C(v, x, y)= P(v, x)+ P(v, y)+ {x, y}, and calculate its length.
    #     Degenerate cases in which P(v, x) and P(v, y) have vertices other
    #     than v in common can be omitted.
    edges = []
    for i_seq,bond_list in enumerate(bond_lists):
      for bond in bond_list:
        j_seq = bond.j_seq
        assert j_seq != i_seq
        if (j_seq > i_seq):
          edges.append((i_seq,j_seq))
    if (0):
      print edges
    cycles = set()
    for v in xrange(n_vertices):
      for x,y in edges:
        if (x == v or y == v): continue
        pvx = shortest_paths[v][x]
        pvy = shortest_paths[v][y]
        if (pvx is None or pvy is None): continue
        if (pvx[0] == x): pvx = list(reversed(pvx))
        if (pvy[0] == v): pvy = list(reversed(pvy))
        if (len(set(pvx[1:] + pvy[:-1])) != len(pvx) + len(pvy) - 2):
          continue
        cycle = pvx + pvy[:-1]
        i = cycle.index(min(cycle))
        if (i != 0): cycle = cycle[i:] + cycle[:i]
        if (cycle[1] > cycle[-1]):
          cycle.reverse()
          cycle = cycle[-1:] + cycle[0:-1]
        cycles.add(tuple(cycle))
    #
    # (3) order cycles by weight
    cycles = list(cycles)
    def cmp_cycles(a, b):
      return cmp(len(a), len(b))
    cycles.sort(cmp_cycles)
    if (0):
      for cycle in cycles:
        print "cycle:", cycle
    #
    if (1):
      # (4) Use the greedy algorithm to find the minimum cycle basis from
      #     this set of cycles.
      #     One method to perform this step is to consider the cycles
      #     as the rows of a 0-1 matrix. The columns correspond to
      #     the edges of the graph; the rows are the incidence vectors
      #     of the cycles. Gaussian elimination using elementary row
      #     operations over the integers modulo 2 can be applied to
      #     the matrix. Each row should be processed in turn, in the
      #     order of the weights of the cycles. When enough independent
      #     cycles have been found, the process can stop.
      edge_indices = {}
      for i,e in enumerate(edges):
        edge_indices[e] = i
      matrix = []
      for cycle in cycles:
        row = [0] * len(edges)
        for x,y in zip(cycle, cycle[1:]+cycle[:1]):
          if (x > y): x,y = y,x
          i = edge_indices[(x,y)]
          row[i] = 1
        matrix.append(row)
        print "m:", row
      free_vars, row_perm = mod2_row_echelon_form(m=matrix)
      cb_rank = len(matrix[0]) - len(free_vars)
      cycle_basis = []
      for i,i_cycle,row in zip(count(),row_perm, matrix):
        if (i < cb_rank):
          print i_cycle, row
          cycle_basis.append(cycles[i_cycle])
          assert row.count(1) >= len(cycles[0])
        elif (i < 2*cb_rank or i == len(matrix)-1):
          print i_cycle, len(cycles[i_cycle])
          assert row == [0] * len(matrix[0])
        elif (i == 2*cb_rank):
          print "..."
      print "cb_rank:", cb_rank
    #
    have_vertex = [False] * n_vertices
    vertex_cycle_basis = []
    for cycle in cycles:
      keep = False
      for v in cycle:
        if (not have_vertex[v]):
          have_vertex[v] = True
          keep = True
      if (keep):
        vertex_cycle_basis.append(cycle)
        print "vertex keep:", cycle
    #
    have_edge = {}
    for i,e in enumerate(edges):
      have_edge[e] = False
    edge_cycle_basis = []
    for cycle in cycles:
      keep = False
      for x,y in zip(cycle, cycle[1:]+cycle[:1]):
        if (x > y): x,y = y,x
        if (not have_edge[(x,y)]):
          have_edge[(x,y)] = True
          keep = True
      if (keep):
        edge_cycle_basis.append(cycle)
        print "edge keep:", cycle
    #
    vertex_cycle_counts = [0] * n_vertices
    for cycle in edge_cycle_basis:
      for v in cycle:
        vertex_cycle_counts[v] += 1
    print "vertex_cycle_counts:", vertex_cycle_counts

class eve_expr_mixin(object):

  def __abs__(self):
    return 1

  def __lt__(self, other):
    return False

  def __gt__(self, other):
    return False

  def __sub__(self, other):
    if (isinstance(other, int)):
      assert other == 0
    else:
      assert isinstance(other, eve_expr_mixin)
    return eve_expr("-", self, other)
    return self

  def __rsub__(self, other):
    assert isinstance(other, int)
    return eve_expr("-", 0, self)

  def __mul__(self, other):
    if (isinstance(other, int)):
      assert other == 0
      return 0
    else:
      assert isinstance(other, eve_expr_mixin)
    return eve_expr("*", self, other)

  def __rmul__(self, other):
    if (isinstance(other, int)):
      if (other == 0): return 0
      if (other == 1): return self
      assert other == -1
      return self.negate()
    return eve_expr("*", other, self)

  def __repr__(self):
    return "[%s%s%s]" % (self.lhs, self.op, self.rhs)

class eve_expr(eve_expr_mixin):

  def __init__(self, op, lhs, rhs):
    self.op = op
    self.lhs = lhs
    self.rhs = rhs

class edge_vector_element(eve_expr_mixin):

  def __init__(self, vector, i_dim):
    self.vector = vector
    self.i_dim = i_dim

  def negate(self):
    return edge_vector_element(vector=self.vector.swap(), i_dim=self.i_dim)

  def __repr__(self):
    v = self.vector
    result = "(%d-%d)%s" % (v.i_seq, v.j_seq, "xyz"[self.i_dim])
    return result

class edge_vector(object):

  def __init__(self, i_seq, j_seq):
    self.i_seq = i_seq
    self.j_seq = j_seq

  def swap(self):
    return edge_vector(self.j_seq, self.i_seq)

  def __getitem__(self, i_dim):
    assert i_dim in [0,1,2]
    return edge_vector_element(vector=self, i_dim=i_dim)

def mod2_row_echelon_form(m):
  n_rows = len(m)
  n_cols = len(m[0])
  free_vars = []
  row_perm = range(n_rows)
  piv_r = 0
  piv_c = 0
  while (piv_c < n_cols):
    best_r = None
    for i_row in xrange(piv_r, n_rows):
      if (m[i_row][piv_c]):
        best_r = i_row
        break
    if (best_r is not None):
      if (best_r != piv_r):
        m[piv_r], m[best_r] = m[best_r], m[piv_r]
        row_perm[piv_r], row_perm[best_r] = row_perm[best_r], row_perm[piv_r]
      for r in xrange(0, n_rows):
        if (r == piv_r): continue
        if (m[r][piv_c] == 0): continue
        for c in xrange(piv_c, n_cols):
          m[r][c] = int(m[r][c] != m[piv_r][c])
      piv_r += 1
    else:
      free_vars.append(piv_c)
    piv_c += 1
  return free_vars, row_perm

def srm_row_echelon_form(m):
  floating_point = isinstance(m[0][0], float)
  edge_algebra = isinstance(m[0][0], edge_vector_element)
  pivot_values = []
  free_vars = []
  n_rows = len(m)
  n_cols = len(m[0])
  piv_r = 0
  piv_c = 0
  while (piv_c < n_cols):
    # search for best pivot
    best_r = None
    if (floating_point):
      max_v = 1.e-12
      for i_row in xrange(piv_r, n_rows):
        v = abs(m[i_row][piv_c])
        if (v > max_v):
          max_v = v
          best_r = i_row
    else:
      min_v = 0
      for i_row in xrange(piv_r, n_rows):
        v = abs(m[i_row][piv_c])
        if (v != 0 and (min_v == 0 or v < min_v)):
          min_v = v
          best_r = i_row
    if (best_r is not None):
      if (best_r != piv_r):
        m[piv_r], m[best_r] = m[best_r], m[piv_r]
      fp = m[piv_r][piv_c]
      for r in xrange(piv_r+1, n_rows):
        fr = m[r][piv_c]
        if (fr == 0): continue
        g = 0
        for c in xrange(piv_c, n_cols):
          if (floating_point):
            m[r][c] = m[r][c] - m[piv_r][c] * fr / fp
          else:
            m[r][c] = m[r][c] * fp - m[piv_r][c] * fr
            if (not edge_algebra):
              g = gcd(m[r][c], g)
        if (g > 1):
          for c in xrange(piv_c, n_cols):
            m[r][c] //= g
      piv_r += 1
      pivot_values.append(fp)
    else:
      free_vars.append(piv_c)
    piv_c += 1
  return pivot_values, free_vars

def construct_secondary_graphs(edge_set, edge_lists):
  done = [False] * len(edge_lists)
  secondary_graphs = []
  for i_seq in xrange(len(edge_lists)):
    if (done[i_seq]): continue
    secondary_edge_set = set()
    def traverse(i_seq):
      done[i_seq] = True
      j_seqs = edge_lists[i_seq]
      for j1 in xrange(0,len(j_seqs)-1):
        j_seq1 = j_seqs[j1]
        for j2 in xrange(j1+1,len(j_seqs)):
          j_seq2 = j_seqs[j2]
          def norm_edge(i,j):
            if (i < j): return (i,j)
            return (j,i)
          e = norm_edge(j_seq1, j_seq2)
          if (not e in edge_set and not e in secondary_edge_set):
            secondary_edge_set.add(e)
      for j_seq in j_seqs:
        if (not done[j_seq]):
          traverse(i_seq=j_seq)
    traverse(i_seq=i_seq)
    if (len(secondary_edge_set) != 0):
      secondary_graphs.append(secondary_edge_set)
  print "number of graphs:", len(secondary_graphs)
  for secondary_edge_set in secondary_graphs:
    print "  len(secondary_edge_set):", len(secondary_edge_set)
  return secondary_graphs

def process_code_delete_and_add_edge_expressions(
      code,
      delete_expressions,
      add_edge_expressions):
  delete_expressions = list(delete_expressions)
  add_edge_expressions = list(add_edge_expressions)
  ie = None
  de = []
  aee = []
  fld = None
  def store_field():
    if (fld is not None):
      if (fld[0] == "-"): de.append(fld[1:])
      else: aee.append(fld[1:])
  for i,c in enumerate(code):
    if (c in ["+","-"]):
      if (ie is None): ie = i
      store_field()
      fld = c
    elif (fld is not None):
      fld += c
  store_field()
  if (ie is not None):
    code = code[:ie]
  de.reverse()
  for e in de:
    delete_expressions.insert(0, e)
  aee.reverse()
  for e in aee:
    add_edge_expressions.insert(0, e)
  return code, delete_expressions, add_edge_expressions

class process(object):

  def __init__(self,
      code,
      attach_inverse_pivots=[],
      delete_expressions=[],
      add_edge_expressions=[]):
    self.pdb_file_name = None
    self.atom_attributes_list = None
    self.atom_list = []
    self.bond_lists = []
    self._edge_lists = None
    self.secondary_graphs = []
    self.hinges = []
    self.potential_implicit_edges = []
    self.angle_list = []
    self.dihedral_list = []
    self.special_labels = []
    code, delete_expressions, add_edge_expressions = \
      process_code_delete_and_add_edge_expressions(
        code=code,
        delete_expressions=delete_expressions,
        add_edge_expressions=add_edge_expressions)
    flds = code.split(":")
    code = flds[0]
    attach_inverse_pivots = list(attach_inverse_pivots)
    for fld in reversed(flds[1:]):
      attach_inverse_pivots.insert(0, int(fld))
    s = ":".join([code] + [str(pivot) for pivot in attach_inverse_pivots])
    if (len(add_edge_expressions) != 0):
      s = "+".join([s] + add_edge_expressions)
    if (len(delete_expressions) != 0):
      s = "-".join([s] + delete_expressions)
    print 'Code: "%s"' % s
    if (code == "triangle"):
      self.construct_triangle()
    elif (code == "sqtri"):
      self.construct_sqtri()
    elif (code == "cube"):
      self.construct_cube()
    elif (code == "cube_oct"):
      self.construct_cube_oct()
    elif (code == "p120"):
      self.construct_p120()
    elif (code == "tet"):
      self.construct_tetrahedron()
    elif (code == "oct"):
      self.construct_octahedron()
    elif (code == "rho"):
      self.construct_rhombic_dodecahedron()
    elif (code == "dod"):
      self.construct_dodecahedron()
    elif (code == "tri"):
      self.construct_triacontahedron()
    elif (code == "ico"):
      self.construct_icosahedron()
    elif (code.startswith("ico")):
      level = int(code[3:])
      self.construct_icosahedron(level=level)
    elif (code == "bucky"):
      self.construct_bucky_ball()
    elif (code == "soct"):
      self.construct_split_oct()
    elif (code == "toct"):
      self.construct_truncated_oct()
    elif (code == "gyro"):
      self.construct_gyrobifastigium()
    elif (len(code) > 3 and code.startswith("tet") and code[3] in "123456789"):
      self.construct_tetn(n=int(code[3:]))
    elif (len(code) > 3 and code.startswith("rig") and code[3] in "123456789"):
      self.construct_rign(n=int(code[3:]))
    elif (code.startswith("loop")):
      level = int(code[4:])
      self.construct_loop(level=level)
    elif (code.startswith("chain")):
      level = int(code[5:])
      self.construct_loop(level=level, open=True)
    elif (code.startswith("prism")):
      level = int(code[5:])
      self.construct_prism(level=level)
    elif (code.startswith("fan")):
      level = int(code[3:])
      self.construct_fan(level=level)
    elif (code.startswith("shell")):
      level = int(code[5:])
      self.construct_shell(level=level)
    elif (code.startswith("pivot")):
      level = int(code[5:])
      self.construct_pivot(level=level)
    elif (code.startswith("loop")):
      level = int(code[4:])
      self.construct_loop(level=level)
    elif (code.startswith("chain")):
      level = int(code[5:])
      self.construct_loop(level=level, open=True)
    elif (code.startswith("prism")):
      level = int(code[5:])
      self.construct_prism(level=level)
    elif (code.startswith("fan")):
      level = int(code[3:])
      self.construct_fan(level=level)
    elif (code.startswith("shell")):
      level = int(code[5:])
      self.construct_shell(level=level)
    elif (code.startswith("pivot")):
      level = int(code[5:])
      self.construct_pivot(level=level)
    elif (code.startswith("barrel")):
      level = int(code[6:])
      self.construct_barrel(level=level)
    elif (code.startswith("bcyc")):
      level = int(code[4:])
      self.construct_banana_cycle(level=level)
    elif (code == "mt1996"):
      self.construct_mt1996()
    elif (code == "cluster"):
      self.construct_tetrahedra_cluster()
    elif (code.startswith("special")):
      level = int(code[7:])
      self.construct_special(level=level)
    elif (code.endswith(".pdb") or code.endswith(".ent")):
      self.pdb_file_name = code
      self.convert_pdb(file_name=code)
    else:
      self.convert_elbow_pickle(code=code)
    for pivot in attach_inverse_pivots:
      self.attach_inverse(pivot=pivot)
    self.delete(expressions=delete_expressions)
    self.add_custom_edges(expressions=add_edge_expressions)

  def add_atom(self, site, label=None):
    if (label is None):
      label = "V" + str(len(self.atom_list))
    self.atom_list.append(
      atom(label=label, element=label, site=matrix.col(site)))

  def init_bond_lists(self):
    assert len(self.bond_lists) == 0
    for i_seq in xrange(len(self.atom_list)):
      self.bond_lists.append([])

  def add_bond(self, (i,j), distance_ideal=1):
    self.bond_lists[i].append(bond(j_seq=j, distance_ideal=distance_ideal))
    self.bond_lists[j].append(bond(j_seq=i, distance_ideal=distance_ideal))

  def edge_lists(self):
    if (self._edge_lists is None):
      self._edge_lists = []
      for bond_list in self.bond_lists:
        self._edge_lists.append([bond.j_seq for bond in bond_list])
    return self._edge_lists

  def edge_iterator(self):
    for i_seq,bond_list in enumerate(self.bond_lists):
      for bond in bond_list:
        j_seq = bond.j_seq
        assert j_seq != i_seq
        if (j_seq < i_seq): continue
        yield (i_seq, j_seq)

  def attach_inverse(self, pivot):
    assert pivot >= 0
    al = self.atom_list
    n = len(al)
    assert pivot < n
    edges = list(self.edge_iterator())
    self.bond_lists = []
    two_pivot_site = 2 * al[pivot].site
    for i in xrange(n):
      if (i == pivot): continue
      self.add_atom(site=two_pivot_site-al[i].site)
    self.init_bond_lists()
    for edge in edges:
      self.add_bond(edge)
      def inv_e(i):
        if (i < pivot): return i + n
        if (i > pivot): return i + n - 1
        return i
      self.add_bond([inv_e(i) for i in edge])

  def delete(self, expressions):
    vertex_selection = set()
    edge_selection = set()
    for expr in expressions:
      def raise_invalid():
        raise RuntimeError("Invalid delete expression: %s" % expr)
      try: flds = eval("["+expr+"]", {}, {})
      except KeyboardInterrupt: raise
      except: raise_invalid()
      for fld in flds:
        if (isinstance(fld, int)):
          vertex_selection.add(fld)
        elif (isinstance(fld, tuple)):
          assert len(fld) == 2
          edge_selection.add(tuple(sorted(fld)))
        else:
          raise_invalid()
    self.delete_edges(selection=edge_selection)
    self.delete_vertices(selection=vertex_selection)

  def add_custom_edges(self, expressions):
    edges = set()
    for expr in expressions:
      def raise_invalid():
        raise RuntimeError("Invalid add-edge expression: %s" % expr)
      try: flds = eval("["+expr+"]", {}, {})
      except KeyboardInterrupt: raise
      except: raise_invalid()
      for fld in flds:
        if (isinstance(fld, tuple)):
          assert len(fld) == 2
          edges.add(tuple(sorted(fld)))
        else:
          raise_invalid()
    for e in edges:
      self.add_bond(e)

  def delete_edges(self, selection):
    def rm(i, j):
      for k,b in enumerate(self.bond_lists[i]):
        if (b.j_seq == j):
          del self.bond_lists[i][k]
          return
      raise RuntimeError("Non-existing edge: (%d,%d)" % (i,j))
    for i,j in selection:
      rm(i,j)
      rm(j,i)

  def delete_vertices(self, selection):
    for i_sel in reversed(sorted(selection)):
      del self.atom_list[i_sel]
      for ibl,bl in enumerate(self.bond_lists):
        if (ibl == i_sel): continue
        ib_del = None
        for ib,b in enumerate(bl):
          if (b.j_seq == i_sel):
            assert ib_del is None
            ib_del = ib
          elif (b.j_seq > i_sel):
            b.j_seq -= 1
        if (ib_del is not None):
          del bl[ib_del]
      del self.bond_lists[i_sel]

  def extract_distances(self):
    result = []
    al = self.atom_list
    for i_seq in xrange(len(al)):
      result.append({})
    for i_seq,j_seq in self.edge_iterator():
      result[i_seq][j_seq] = abs(al[i_seq].site - al[j_seq].site)
    return result

  def construct_triangle(self):
    for x,y in [(0,0),(1,0),(1,1)]:
      self.add_atom((x,y,0))
    self.init_bond_lists()
    for i,j in [(0,1),(1,2),(2,0)]:
      self.add_bond((i,j))

  def construct_sqtri(self):
    for x,y in [(0,0),(1,0),(1,1), (0,1)]:
      self.add_atom((x,y,0))
    self.init_bond_lists()
    for i,j in [(0,1),(1,2),(2,3),(3,0),(3,1)]:
      self.add_bond((i,j))

  def construct_cube(self):
    for x in [0,1]:
      for y in [0,1]:
        for z in [0,1]:
          self.add_atom((x,y,z))
    self.init_bond_lists()
    for i,j in [(0,1),(0,2),(1,3),(2,3),
                (4,5),(4,6),(5,7),(6,7),
                (0,4),(1,5),(2,6),(3,7),
                # each body-diagonal removes 1 dof
                (0,7),(1,6),(2,5), # (3,4) is redundant
                # each face-diagonal removes 1 dof
                (0,6),(0,3),(0,5)][:12]:
      self.add_bond((i,j))

  def construct_cube_oct(self):
    for x in [0,1]:
      for y in [0,1]:
        for z in [0,1]:
          self.add_atom((x,y,z))
    self.add_atom((-0.5,0.5,0.5))
    self.add_atom((1.5,0.5,0.5))
    self.init_bond_lists()
    for i,j in [(0,1),(0,2),(1,3),(2,3),
                (4,5),(4,6),(5,7),(6,7),
                (0,4),(1,5),(2,6),(3,7),
                (0,8),(1,8),(2,8),(3,8),
                (4,9),(5,9),(6,9),(7,9)]:
      self.add_bond((i,j))

  def bonds_from_sites(self,
        sites,
        cutoff_level=0,
        distance_relative_tolerance=1.e-5):
    print "Number of points:", sites.size()
    for site in sites:
      self.add_atom(site)
    distances = flex.sqrt((sites[1:] - sites[0]).dot())
    distances = distances.select(flex.sort_permutation(data=distances))
    scale = 1 / distances[0]
    sites *= scale
    distances *= scale
    flds = ["%.6g" % v for v in distances[:10]]
    if (len(distances) > 10): flds.append("...")
    print "distances:", ", ".join(flds)
    asu_mappings = crystal.direct_space_asu.non_crystallographic_asu_mappings(
      sites_cart=sites)
    pair_generator = crystal.neighbors_fast_pair_generator(
      asu_mappings=asu_mappings,
      distance_cutoff=distances[cutoff_level]*(1+distance_relative_tolerance))
    self.init_bond_lists()
    for pair in pair_generator:
      self.add_bond((pair.i_seq, pair.j_seq))

  def construct_p120(self, vertex_indices=None):
    # http://www.rwgrayprojects.com/Lynn/Coordinates/coord01.html
    vertices_table = """\
1       A       0       0       2p^2
2       B       p^2     0       p^3
3       A       p       p^2     p^3
4       C       0       p       p^3
5       A       -p      p^2     p^3
6       B       -p^2    0       p^3
7       A       -p      -p^2    p^3
8       C       0       -p      p^3
9       A       p       -p^2    p^3
10      A       p^3     p       p^2
11      C       p^2     p^2     p^2
12      B       0       p^3     p^2
13      C       -p^2    p^2     p^2
14      A       -p^3    p       p^2
15      A       -p^3    -p      p^2
16      C       -p^2    -p^2    p^2
17      B       0       -p^3    p^2
18      C       p^2     -p^2    p^2
19      A       p^3     -p      p^2
20      C       p^3     0       p
21      A       p^2     p^3     p
22      A       -p^2    p^3     p
23      C       -p^3    0       p
24      A       -p^2    -p^3    p
25      A       p^2     -p^3    p
26      A       2p^2    0       0
27      B       p^3     p^2     0
28      C       p       p^3     0
29      A       0       2p^2    0
30      C       -p      p^3     0
31      B       -p^3    p^2     0
32      A       -2p^2   0       0
33      B       -p^3    -p^2    0
34      C       -p      -p^3    0
35      A       0       -2p^2   0
36      C       p       -p^3    0
37      B       p^3     -p^2    0
38      C       p^3     0       -p
39      A       p^2     p^3     -p
40      A       -p^2    p^3     -p
41      C       -p^3    0       -p
42      A       -p^2    -p^3    -p
43      A       p^2     -p^3    -p
44      A       p^3     p       -p^2
45      C       p^2     p^2     -p^2
46      B       0       p^3     -p^2
47      C       -p^2    p^2     -p^2
48      A       -p^3    p       -p^2
49      A       -p^3    -p      -p^2
50      C       -p^2    -p^2    -p^2
51      B       0       -p^3    -p^2
52      C       p^2     -p^2    -p^2
53      A       p^3     -p      -p^2
54      B       p^2     0       -p^3
55      A       p       p^2     -p^3
56      C       0       p       -p^3
57      A       -p      p^2     -p^3
58      B       -p^2    0       -p^3
59      A       -p      -p^2    -p^3
60      C       0       -p      -p^3
61      A       p       -p^2    -p^3
62      A       0       0       -2p^2
"""
    edge_table = """\
{ 1, 2}, { 1, 4}, { 1, 6}, { 1, 8}, { 2, 3}, { 2, 4}, { 2, 8},
{ 2, 9}, { 2, 10}, { 2, 11}, { 2, 18}, { 2, 19}, { 2, 20}, { 3, 4},
{ 3, 11}, { 3, 12}, { 4, 5}, { 4, 6}, { 4, 12}, { 5, 6}, { 5, 12},
{ 5, 13}, { 6, 7}, { 6, 8}, { 6, 13}, { 6, 14}, { 6, 15}, { 6, 16},
{ 6, 23}, { 7, 8}, { 7, 16}, { 7, 17}, { 8, 9}, { 8, 17}, { 9, 17},
{ 9, 18}, {10, 11}, {10, 20}, {10, 27}, {11, 12}, {11, 21}, {11, 27},
{12, 13}, {12, 21}, {12, 28}, {12, 29}, {12, 22}, {12, 30}, {13, 14},
{13, 22}, {13, 31}, {14, 23}, {14, 31}, {15, 16}, {15, 23}, {15, 33},
{16, 17}, {16, 24}, {16, 33}, {17, 18}, {17, 24}, {17, 25}, {17, 34},
{17, 35}, {17, 36}, {18, 19}, {18, 25}, {18, 37}, {19, 20}, {19, 37},
{20, 26}, {20, 27}, {20, 37}, {21, 27}, {21, 28}, {22, 30}, {22, 31},
{23, 31}, {23, 32}, {23, 33}, {24, 33}, {24, 34}, {25, 36}, {25, 37},
{26, 27}, {26, 37}, {26, 38}, {27, 28}, {27, 38}, {27, 39}, {27, 44},
{27, 45}, {28, 29}, {28, 39}, {28, 46}, {29, 30}, {29, 46}, {30, 31},
{30, 40}, {30, 46}, {31, 32}, {31, 40}, {31, 41}, {31, 47}, {31, 48},
{32, 33}, {32, 41}, {33, 34}, {33, 41}, {33, 42}, {33, 49}, {33, 50},
{34, 35}, {34, 42}, {34, 51}, {35, 36}, {35, 51}, {36, 37}, {36, 43},
{36, 51}, {37, 38}, {37, 43}, {37, 52}, {37, 53}, {38, 44}, {38, 53},
{38, 54}, {39, 45}, {39, 46}, {40, 46}, {40, 47}, {41, 48}, {41, 49},
{41, 58}, {42, 50}, {42, 51}, {43, 51}, {43, 52}, {44, 45}, {44, 54},
{45, 55}, {45, 46}, {46, 47}, {46, 55}, {46, 56}, {46, 57}, {47, 48},
{47, 57}, {47, 58}, {48, 58}, {49, 50}, {49, 58}, {50, 51}, {50, 58},
{50, 59}, {51, 52}, {51, 59}, {51, 60}, {51, 61}, {52, 53}, {52, 61},
{52, 54}, {53, 54}, {54, 55}, {54, 56}, {54, 60}, {54, 61}, {54, 62},
{55, 56}, {56, 57}, {56, 58}, {56, 62}, {57, 58}, {58, 59}, {58, 60},
{58, 62}, {59, 60}, {60, 61}, {60, 62}
"""
    for i,line in enumerate(vertices_table.splitlines()):
      flds = line.replace("^","**").split()
      assert flds[0] == str(i+1)
      assert flds[1] in ["A", "B", "C"]
      self.add_atom(site=[
        eval(s.replace("2p","2*p").replace("^","**"),{"p": golden_ratio},{})
          for s in flds[2:]])
    if (vertex_indices is None):
      self.init_bond_lists()
      for line in edge_table.splitlines():
        if (line[-1] != ","): line += ","
        for pair in line.replace(" ","").replace("{","").split("},"):
          if (pair == ""): continue
          i,j = [int(s)-1 for s in pair.split(",")]
          self.add_bond((i,j))
      if (0):
        self.add_bond((29-1,35-1))
    else:
      sites = flex.vec3_double([a.site for a in self.atom_list])
      self.atom_list = []
      self.bonds_from_sites(
        sites=sites.select(flex.size_t(vertex_indices)-1))

  def construct_tetrahedron(self):
    self.construct_p120(vertex_indices=[
      4, 34, 38, 47])

  def construct_octahedron(self):
    self.construct_p120(vertex_indices=[
      7, 10, 22, 43, 49, 55])

  def construct_rhombic_dodecahedron(self):
    self.construct_p120(vertex_indices=[
      4, 7, 10, 18, 22, 23, 28, 34, 38, 43, 47, 49, 55, 60])

  def construct_dodecahedron(self):
    self.construct_p120(vertex_indices=[
      4, 8, 11, 13, 16, 18, 20, 23, 28, 30,
      34, 36, 38, 41, 45, 47, 50, 52, 56, 60])

  def construct_triacontahedron(self):
    self.construct_p120(vertex_indices=[
      2, 4, 6, 8, 11, 12, 13, 16, 17, 18, 20, 23,
      27, 28, 30, 31, 33, 34, 36, 37, 38, 41, 45, 46,
      47, 50, 51, 52, 54, 56, 58, 60])

  def construct_icosahedron(self, level=None):
    if (level is None):
      self.construct_p120(vertex_indices=[
        2, 6, 12, 17, 27, 31, 33, 37, 46, 51, 54, 58])
    else:
      ico = scitbx.math.icosahedron(level=level)
      self.bonds_from_sites(sites=ico.sites, cutoff_level=level+1)

  def construct_bucky_ball(self):
    f = golden_ratio
    self.bonds_from_sites(
      sites=flex.vec3_double([
        (0,1,3*f),
        (0,1,-3*f),
        (0,-1,3*f),
        (0,-1,-3*f),
        (1,3*f,0),
        (1,-3*f,0),
        (-1,3*f,0),
        (-1,-3*f,0),
        (3*f,0,1),
        (3*f,0,-1),
        (-3*f,0,1),
        (-3*f,0,-1),
        (2,(1+2*f),f),
        (2,(1+2*f),-f),
        (2,-(1+2*f),f),
        (2,-(1+2*f),-f),
        (-2,(1+2*f),f),
        (-2,(1+2*f),-f),
        (-2,-(1+2*f),f),
        (-2,-(1+2*f),-f),
        ((1+2*f),f,2),
        ((1+2*f),f,-2),
        ((1+2*f),-f,2),
        ((1+2*f),-f,-2),
        (-(1+2*f),f,2),
        (-(1+2*f),f,-2),
        (-(1+2*f),-f,2),
        (-(1+2*f),-f,-2),
        (f,2,(1+2*f)),
        (f,2,-(1+2*f)),
        (f,-2,(1+2*f)),
        (f,-2,-(1+2*f)),
        (-f,2,(1+2*f)),
        (-f,2,-(1+2*f)),
        (-f,-2,(1+2*f)),
        (-f,-2,-(1+2*f)),
        (1,(2+f),2*f),
        (1,(2+f),-2*f),
        (1,-(2+f),2*f),
        (1,-(2+f),-2*f),
        (-1,(2+f),2*f),
        (-1,(2+f),-2*f),
        (-1,-(2+f),2*f),
        (-1,-(2+f),-2*f),
        ((2+f),2*f,1),
        ((2+f),2*f,-1),
        ((2+f),-2*f,1),
        ((2+f),-2*f,-1),
        (-(2+f),2*f,1),
        (-(2+f),2*f,-1),
        (-(2+f),-2*f,1),
        (-(2+f),-2*f,-1),
        (2*f,1,(2+f)),
        (2*f,1,-(2+f)),
        (2*f,-1,(2+f)),
        (2*f,-1,-(2+f)),
        (-2*f,1,(2+f)),
        (-2*f,1,-(2+f)),
        (-2*f,-1,(2+f)),
        (-2*f,-1,-(2+f))]))

  def construct_split_oct(self):
    # J. D. Horton, SIAM J. Comput. Vol. 16, No. 2, April 1987
    # Fig. 1
    aa = self.add_atom
    aa((0,0,0.2))
    aa((1,0,0.2))
    aa((1,1,0))
    aa((0,1,0))
    aa((0,0,-0.2))
    aa((1,0,-0.2))
    aa((0.5,0.5,1))
    aa((0.5,0.5,-1))
    self.init_bond_lists()
    for i,j in [(0,1),(1,2),(2,3),(3,0),
                (4,5),(5,2),(3,4),
                (0,6),(1,6),(2,6),(3,6),
                (4,7),(5,7),(2,7),(3,7)]:
      self.add_bond((i,j))

  def construct_truncated_oct(self):
    vertices = []
    base = [(0,1,2),(0,-1,2),(0,1,-2),(0,-1,-2)]
    for i,j,k in [(0,1,2),(0,2,1),(1,0,2),(1,2,0),(2,0,1),(2,1,0)]:
      for v in base:
        self.add_atom((v[i],v[j],v[k]))
    self.init_bond_lists()
    for i,j in [(0,9),(1,9),(1,8),(0,8),(9,18),(18,22),(13,22),(13,4),(4,0),
                (4,12),(12,20),(20,16),(16,8),(13,5),(5,12),(5,2),(2,10),
                (10,17),(17,20),(16,21),(21,17),(21,14),(14,6),(6,1),(14,7),
                (7,15),(15,6),(18,23),(23,15),(2,11),(11,19),(19,22),(19,23),
                (11,3),(3,10),(3,7)]:
      self.add_bond((i,j))

  def construct_gyrobifastigium(self):
    for v in [(0,0,0),(1,0,0),(1,1,0),(0,1,0),
              (0.5,0,0.5),(0.5,1,0.5),
              (0,0.5,-0.5),(1,0.5,-0.5)]:
      self.add_atom(v)
    self.init_bond_lists()
    for i,j in [(0,1),(1,2),(2,3),(3,0),(0,4),(1,4),(2,5),(3,5),(4,5),
                (0,6),(3,6),(1,7),(2,7),(6,7)]:
      self.add_bond((i,j))

  def construct_tetn(self, n):
    assert n >= 4
    points = [
      (0,0,0),
      (-1,1,0),
      (0,1,1),
      (-1,0,1),
      (0,1,0),
      (-1,0,0),
      (0,0,1),
      (-1,1,1),
      (-0.5,0.5,-0.25),
      (-0.5,0.5,1.25),
      (0.25,0.5,0.5),
      (-1.25,0.5,0.5)]
    for v in points[:n]:
      self.add_atom(v)
    self.init_bond_lists()
    for i,j in [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3),
                (0,4),(1,4),(2,4),
                (0,5),(1,5),(3,5),
                (0,6),(2,6),(3,6),
                (1,7),(2,7),(3,7),
                (0,8),(1,8),(4,8),
                (2,9),(3,9),(6,9),
                (4,10),(6,10),(0,10),
                (5,11),(7,11),(1,11)][:6+(n-4)*3]:
      self.add_bond((i,j))

  def construct_rign(self, n):
    assert n > 0
    for x,y in [(0,0),(1,0),(1,1)][:n]:
      self.add_atom((x,y,0))
    for j in xrange(3,n):
      self.add_atom((0.75,0.25,j*0.2))
    self.init_bond_lists()
    for i,j in [(0,1),(1,2),(2,0)][:{1:0,2:1}.get(n,3)]:
      self.add_bond((i,j))
    for j in xrange(3,n):
      for i in xrange(3):
        self.add_bond((i,j))

  def construct_loop(self, level, open=False):
    if (not open):
      assert level >= 3
    else:
      assert level >= 1
    omega = 2 * math.pi / level
    radius = 1 / omega
    for i in xrange(level):
      angle = i * omega
      self.add_atom(
        site=radius*matrix.col((math.cos(angle), math.sin(angle), 0)))
    if (0):
      self.add_atom((0,0,1))
      #self.add_atom((0,0,1))
      #self.add_atom((0,0,1))
      #self.add_atom((0,0,1))
    self.init_bond_lists()
    for i in xrange(level):
      j = (i+1) % level
      if (j == 0 and open): break
      self.add_bond((i,j))
    if (0):
      self.add_bond((0,4))
      self.add_bond((1,4))
      #self.add_bond((1,5))
      #self.add_bond((2,5))
      self.add_bond((2,4))
      #self.add_bond((2,6))
      ##self.add_bond((3,6))
      ###self.add_bond((3,5))
      self.add_bond((3,4))
      #self.add_bond((3,7))
      #self.add_bond((0,7))
      ##self.add_bond((0,6))
      ###self.add_bond((0,5))
      """
      - build all loops and assign new vertex labels
      - join loops:
        - make two labels the same (reduction in dof)
        - propagate label change to bond list
          and remove redundant bonds (increase in dof)
        - check if we implicitly joined in other loops (reduction in dof)
      """

  def construct_prism(self, level):
    omega = 2 * math.pi / level
    radius = 1 / omega
    for z in [0,1]:
      for i in xrange(level):
        angle = i * omega
        self.add_atom(
          site=radius*matrix.col((math.cos(angle), math.sin(angle), z)))
    self.init_bond_lists()
    for offs in [0,level]:
      for i in xrange(level):
        j = (i+1) % level
        self.add_bond((i+offs,j+offs))
    for i in xrange(level):
      self.add_bond((i,i+level))

  def construct_fan(self, level):
    self.construct_shell(level=level, fan_only=True)

  def construct_shell(self, level, fan_only=False, all_internal_edges=False):
    assert level >= 3
    self.add_atom((0,0,1))
    self.add_atom((0,0,-1))
    omega = 2 * math.pi / level
    radius = 1 / omega
    for i in xrange(level):
      angle = i * omega
      self.add_atom(
        site=radius*matrix.col((math.cos(angle), math.sin(angle), 0)))
    self.init_bond_lists()
    for i in xrange(2):
      for j in xrange(level):
        self.add_bond((i,j+2))
    if (not fan_only):
      for i in xrange(level):
        j = (i+1) % level
        self.add_bond((i+2,j+2))
    if (fan_only or all_internal_edges):
      self.add_bond((0,1))
    if (all_internal_edges):
      for i in xrange(level):
        for p in xrange(2,level-1):
          j = i + p
          if (j >= level): break
          self.add_bond((i+2,j+2))
    n = level+2
    assert len(self.atom_list) == n
    if (fan_only):
      assert level*2+1 == self.count_edges()
    elif (all_internal_edges):
      assert (n*(n-1))//2 == self.count_edges()

  def construct_pivot(self, level):
    assert level >= 3
    omega = 2 * math.pi / level
    radius = 1 / omega
    for z in [-1, 1]:
      for i in xrange(level):
        angle = i * omega
        self.add_atom(
          site=radius*matrix.col((math.cos(angle), math.sin(angle), z)))
    i = len(self.atom_list)
    self.add_atom(site=(0,0,0))
    self.init_bond_lists()
    for j in xrange(2*level):
      self.add_bond((i,j))
    for i in xrange(level):
      j = (i+1) % level
      self.add_bond((i,j))
      self.add_bond((i+level,j+level))

  def construct_barrel(self, level):
    assert level >= 3
    # Jack E. Graver (2001), Counting on Frameworks, Figure 3.23 (p. 124)
    omega = 2 * math.pi / level
    radius = 1 / omega
    for z in [0, 1]:
      for i in xrange(level):
        angle = i * omega
        self.add_atom(
          site=radius*matrix.col((math.cos(angle), math.sin(angle), z)))
    self.init_bond_lists()
    for i in xrange(level):
      for j in xrange(level):
        if (j == i): continue
        self.add_bond((i,j+level))

  def construct_banana_cycle(self, level):
    assert level >= 2
    omega = 2 * math.pi / (2*level)
    radius = 1 / omega
    for i in xrange(2*level):
      angle = i * omega
      pivot = radius * matrix.col((math.cos(angle), math.sin(angle), 0))
      if (i % 2 == 0):
        self.add_atom(site=pivot)
      else:
        beta = 2 * math.pi / 3
        rbeta = 1 / beta
        for j in xrange(3):
          angleb = j * beta
          shift = rbeta * matrix.col((math.cos(angleb), 0, math.sin(angleb)))
          r = matrix.sqr((
            math.cos(angle), -math.sin(angle), 0,
            math.sin(angle), math.cos(angle), 0,
            0, 0, 1))
          self.add_atom(site=pivot+r*shift)
    self.init_bond_lists()
    for i in xrange(level):
      ip = i*4
      jp = ((i+1)%level)*4
      for k in xrange(3):
        self.add_bond((ip,ip+1+k))
        self.add_bond((jp,ip+1+k))
      for k in xrange(3):
        self.add_bond((ip+1+k,ip+1+(k+1)%3))

  def construct_mt1996(self):
    # H. Maehara and N. Tokushige
    # A Spatial Unit-Bar-Framework Which Is Rigid and Triangle-Free
    # Graphs and Combinatorics (1996) 12:341-344
    aa = self.add_atom
    for label,site in zip("A B C D A' B' C' D'".split(),
                          [(0,0,1),(1,0,1),(1,1,1),(0,1,1),
                           (0,0,0),(1,0,0),(1,1,0),(0,1,0)]):
      aa(site=site, label=label)
    h = 0.5
    s2 = 2**0.5
    hs2 = h * s2
    r2s2 = 1 / (2 * s2)
    aa(site=(h,h,1+hs2), label="P")
    aa(site=(h,h,1-hs2), label="P0")
    aa(site=(h,h,0-hs2), label="Q")
    aa(site=(h,h,0+hs2), label="Q0")
    aa(site=(h,0-hs2,h), label="R")
    aa(site=(h,0+hs2,h), label="R0")
    aa(site=(h,1+hs2,h), label="S")
    aa(site=(h,1-hs2,h), label="S0")
    aa(site=(0-hs2,h,h), label="T")
    aa(site=(0+hs2,h,h), label="T0")
    aa(site=(1+hs2,h,h), label="U")
    aa(site=(1-hs2,h,h), label="U0")
    aa(site=(h,h+r2s2,h+r2s2), label="J")
    aa(site=(h,h-r2s2,h-r2s2), label="J'")
    aa(site=(h-r2s2,h+r2s2,h), label="K")
    aa(site=(h+r2s2,h-r2s2,h), label="K'")
    aa(site=(h-r2s2,h,h+r2s2), label="L")
    aa(site=(h+r2s2,h,h-r2s2), label="L'")
    self.init_bond_lists()
    label_indices = {}
    for i_seq,a in enumerate(self.atom_list):
      label_indices[a.label] = i_seq
    def ab((a,b)):
      self.add_bond((label_indices[a], label_indices[b]))
    for cs,ps in [("A B C D",     "P P0"),
                  ("A' B' C' D'", "Q Q0"),
                  ("A A' B' B",   "R R0"),
                  ("C C' D' D",   "S S0"),
                  ("A A' D' D",   "T T0"),
                  ("B B' C' C",   "U U0"),
                  ("A B C' D'",   "J J'"),
                  ("A A' C' C",   "K K'"),
                  ("A' D' C B",   "L L'")]:
      for p in ps.split():
        for c in cs.split():
          ab((p, c))
    for ps in ["P Q0", "P0 Q", "R S0", "R0 S", "T U0", "T0 U"]:
      ab(ps.split())

  def construct_tetrahedra_cluster(self):
    root = cg3d.build_3_loop()
    vertices = root.compute_node_sites()
    def random_distances():
      return [1+cg3d.random.random() for i in xrange(3)]
    edges = [(0,1),(1,2),(2,0)]
    for ijk in [(0,1,2),
                (0,2,1),
                (0,3,2),
                (0,2,4),
                (0,5,2),
                (0,1,3),
               ][:]:
      tripod = tripod_node(
        points=[vertices[i] for i in ijk],
        distances=random_distances(),
        p3_sign=1)
      vertices.append(tripod.p3)
      l = len(vertices)-1
      for i in ijk:
        edges.append((i,l))
    if (1):
      edges.append((6,7))
    for vertex in vertices:
      self.add_atom(site=vertex)
    self.init_bond_lists()
    for edge in edges:
      self.add_bond(edge)

  def construct_special(self, level):
    if (level == 1):
      # randomly generated, auto-constructed, with manual adjustments
      for site in [(0,0,1),
                   (0,0.866025,-0.5),
                   (0.544331,-0.7698,-0.333333),
                   (0.816497,-0.288675,0.5),
                   (-0.8,0.1,-0.5),
                   (0.544331,0.673575,0.5),
                   (-0.2,-0.2,-0.2),
                   (3.39935e-017,-0.866025,0.5)]:
        self.add_atom(site=site)
      self.init_bond_lists()
      for edge in [(0, 1), (0, 4), (0, 5), (0, 6), (0, 7), (1, 3), (1, 4),
                   (1, 6), (2, 3), (2, 6), (2, 7), (3, 5), (3, 6), (3, 7),
                   (4, 5), (4, 6), (4, 7), (5, 6), (6, 7)]:
        self.add_bond(edge)
    elif (level == 2):
      # mannose atoms C1, C2, O2, C3, C4, C5, O5
      for site in [(26.348,92.216,14.905),
                   (26.925,93.566,15.153),
                   (27.152,93.692,16.546),
                   (28.209,93.649,14.331),
                   (29.196,92.532,14.724),
                   (28.501,91.174,14.747),
                   (27.27,91.289,15.43)]:
        self.add_atom(site=site)
      self.init_bond_lists()
      for edge in [(0,1), (0,6), (1,2), (1,3), (3,4), (4,5), (5,6)]:
        self.add_bond(edge)
    else:
      raise RuntimeError("special%d unknown." % level)

  def convert_pdb(self, file_name):
    from mmtbx.monomer_library import pdb_interpretation
    import mmtbx.monomer_library.server as mon_lib_server
    import iotbx.pdb
    mon_lib_srv = mon_lib_server.server()
    ener_lib = mon_lib_server.ener_lib()
    processed_pdb_file = pdb_interpretation.process(
      mon_lib_srv=mon_lib_srv,
      ener_lib=ener_lib,
      file_name=file_name,
      strict_conflict_handling=True,
      log=sys.stdout)
    pdb_atoms = processed_pdb_file.all_chain_proxies.pdb_atoms
    pdb_atoms_keep = []
    reindexing = [None] * len(pdb_atoms)
    for i,a in enumerate(pdb_atoms):
      if (a.parent().resname+" " in iotbx.pdb.common_residue_names_water):
        continue
      reindexing[i] = len(pdb_atoms_keep)
      pdb_atoms_keep.append(a)
      self.atom_list.append(atom(
        label=a.name,
        element=a.name[:2].strip(),
        site=matrix.col(a.xyz)))
    self.init_bond_lists()
    geo_manager = processed_pdb_file.geometry_restraints_manager()
    bpt = geo_manager.bond_params_table
    for sym_pair in geo_manager.shell_sym_tables[0].iterator():
      assert sym_pair.rt_mx_ji.is_unit_mx()
      i,j = sym_pair.i_seqs()
      ri,rj = reindexing[i], reindexing[j]
      if (ri is None or rj is None): continue
      self.add_bond((ri,rj), distance_ideal=bpt[i][j].distance_ideal)
    self.pdb_atoms = pdb_atoms_keep

  def convert_elbow_pickle(self, code):
    assert dir_pickles is not None
    mol = easy_pickle.load(
      file_name=os.path.join(dir_pickles, "elbow.%s.pickle" % code))
    if (0):
      print mol.DisplayBrief()
      print mol.Display()
      print mol.bonds
    reindexing_map = {}
    if (0 and code == "TBR"):
      mol.TrimMolecule(indices=[1,2,3,13,14,15])
    if (0 and code == "CLF"):
      mol.TrimMolecule(indices=[1,2,4,5,9,10,12])
    for i_seq,a in enumerate(mol):
      assert not reindexing_map.has_key(a.index)
      reindexing_map[a.index] = i_seq
      self.atom_list.append(
        atom(label=a.name, element=a.element, site=matrix.col(a.xyz)))
      print a.name, a.index, i_seq
    print "Number of atoms:", code, len(self.atom_list)
    sys.stdout.flush()
    self.init_bond_lists()
    bond_registry = {}
    for b in mol.bonds:
      i_seqs = [reindexing_map[b[i].index] for i in [0,1]]
      assert i_seqs[0] != i_seqs[1]
      i_seqs.sort()
      if (0 and code == "TBR"):
        if (i_seqs == [4,5]): i_seqs = [1,4]
      if (0 and code == "CUZ"):
        if (i_seqs == [1,3]): continue
      key = tuple(i_seqs)
      assert not key in bond_registry
      bond_registry[key] = None
      self.add_bond((i_seqs[0], i_seqs[1]), distance_ideal=b.equil)
    if (0 and code == "TBR"):
      self.add_bond((0, 5))
    for a in mol.angles:
      if (not hasattr(a, "equil")): continue
      self.angle_list.append(angle(
        i_seqs=[reindexing_map[a[i].index] for i in [0,1,2]],
        angle_ideal=a.equil))
    if (0): # fails for CLF after trim (elbow problem?)
      for d in mol.dihedrals:
        if (not hasattr(d, "equil")): continue
        self.dihedral_list.append(dihedral(
          i_seqs=[reindexing_map[d[i].index] for i in [0,1,2,3]],
          angle_ideal=d.equil))

  def as_graph1(self):
    "Simple depth-first recursion, no sorting"
    root_nodes = []
    serial = [None] * len(self.atom_list)
    self.bonds_forward = []
    self.bonds_back = []
    counter = count()
    al = self.atom_list
    for i_seq in xrange(len(al)):
      if (serial[i_seq] is not None): continue
      root_node = cg3d.root_node(site=al[i_seq].site)
      root_nodes.append(root_node)
      def traverse(parent_i_seq, i_seq):
        serial[i_seq] = counter.next()
        for bond in self.bond_lists[i_seq]:
          if (bond.j_seq == parent_i_seq): continue
          if (serial[bond.j_seq] is None):
            self.bonds_forward.append([i_seq, bond.j_seq])
            traverse(parent_i_seq=i_seq, i_seq=bond.j_seq)
          elif (serial[bond.j_seq] < serial[i_seq]):
            self.bonds_back.append([i_seq, bond.j_seq])
      traverse(parent_i_seq=None, i_seq=i_seq)
    for i_seq in xrange(len(al)):
      al[i_seq].label = str(serial[i_seq]) + " " + al[i_seq].label.strip()
    print "Number of graphs:", len(root_nodes)
    return root_nodes

  def as_graph2(self):
    "Depth-first recursion with sorting"
    number_of_bonds = flex.size_t([len(bond_list)
      for bond_list in self.bond_lists])
    perm_number_of_bonds = flex.sort_permutation(
      data=number_of_bonds, reverse=True)
    number_of_used_bonds = flex.size_t(number_of_bonds.size(), 0)
    root_nodes = []
    serial = [None] * len(self.atom_list)
    self.bonds_forward = []
    self.bonds_back = []
    counter = count()
    al = self.atom_list
    for i_seq in perm_number_of_bonds:
      if (serial[i_seq] is not None): continue
      serial[i_seq] = counter.next()
      def traverse(parent_i_seq, i_seq):
        connected = []
        closing = []
        for bond in self.bond_lists[i_seq]:
          if (bond.j_seq == parent_i_seq): continue
          if (serial[bond.j_seq] is None):
            connected.append(bond)
            number_of_used_bonds[bond.j_seq] += 1
            self.bonds_forward.append([i_seq, bond.j_seq])
          elif (serial[bond.j_seq] < serial[i_seq]):
            closing.append(bond.j_seq)
            self.bonds_back.append([i_seq, bond.j_seq])
        def cmp_connected(a, b):
          c = cmp(number_of_used_bonds[b.j_seq], number_of_used_bonds[a.j_seq])
          if (c != 0): return c
          return cmp(number_of_bonds[b.j_seq], number_of_bonds[a.j_seq])
        connected.sort(cmp_connected)
        for bond in connected:
          serial[bond.j_seq] = counter.next()
        if (len(closing) == 0):
          if (parent_i_seq is None):
            root_node = cg3d.root_node(site=al[i_seq].site)
            root_nodes.append(root_node)
            label_ext = "R"
          else:
            cg3d.chain_node()
            label_ext = "C"
        elif (len(closing) == 1):
          cg3d.loop_node()
          label_ext = "L"
        elif (len(closing) == 2):
          #cg3d.tripod_node()
          label_ext = "T"
        else:
          msg = "Too many closing connections (%d)" % len(closing)
          if (0):
            raise RuntimeError(msg)
          else:
            print msg
          label_ext = "?%d?" % len(closing)
        al[i_seq].label = str(serial[i_seq]) + label_ext \
                        + " "+al[i_seq].label.strip()
        for bond in connected:
          traverse(parent_i_seq=i_seq, i_seq=bond.j_seq)
      traverse(parent_i_seq=None, i_seq=i_seq)
    print "Number of graphs:", len(root_nodes)
    self.check_bonds_accounted_for()
    return root_nodes

  def as_graph3(self):
    "Depth-first recursion with full back-tracking"
    serial = [None] * len(self.atom_list)
    self.bonds_forward = []
    self.bonds_back = []
    atom_list = self.atom_list
    #for i_seq in xrange(len(atom_list)):
    for i_seq in [0]: # XXX
      if (serial[i_seq] is not None): continue
      def traverse(parent_i_seq, i_seq):
        #print "parent_i_seq, i_seq", parent_i_seq, i_seq
        serial[i_seq] = len(self.bonds_forward)
        entry_len_bonds_forward = len(self.bonds_forward)
        entry_len_bonds_back = len(self.bonds_back)
        bond_list = self.bond_lists[i_seq]
        bond_list_perm = flex.size_t_range(len(bond_list))
        while True:
          if (parent_i_seq is None):
            print "  top bond_list_perm", list(bond_list_perm)
          new_bonds_back = 0
          for i_bond in bond_list_perm:
            bond = bond_list[i_bond]
            if (bond.j_seq == parent_i_seq): continue
            if (serial[bond.j_seq] is None):
              self.bonds_forward.append([i_seq, bond.j_seq])
              if (not traverse(parent_i_seq=i_seq, i_seq=bond.j_seq)):
                break
            elif (serial[bond.j_seq] < serial[i_seq]):
              new_bonds_back += 1
              #print "new_bonds_back", new_bonds_back
              if (new_bonds_back > 2):
                break
              self.bonds_back.append([i_seq, bond.j_seq])
              #print "    bonds_back:", self.bonds_back[entry_len_bonds_back:]
          else:
            #print "  return True"
            return True
          #print "del self.bonds_back[%d:]" % entry_len_bonds_back
          #print "del self.bonds_forward[%d:]" % entry_len_bonds_forward
          del self.bonds_back[entry_len_bonds_back:]
          del self.bonds_forward[entry_len_bonds_forward:]
          if (not bond_list_perm.next_permutation()):
            break
        serial[i_seq] = None
        #print "  return False"
        return False
      traverse_stat = traverse(parent_i_seq=None, i_seq=i_seq)
      print "top-level traverse returns:", traverse_stat
    for i_seq in xrange(len(atom_list)):
      atom_list[i_seq].label = str(serial[i_seq]) \
                             + " " + atom_list[i_seq].label.strip()
      if (traverse_stat):
        print "serial:label:", atom_list[i_seq].label
    return None

  def as_graph4(self, show_bond_back=False):
    "Breadth-first recursion with sorting"
    atom_list = self.atom_list
    serial = [None] * len(atom_list)
    self.bonds_forward = []
    self.bonds_back = []
    self.degrees_of_freedom = [3] * len(atom_list)
    self.shell_number = [0] * len(atom_list)
    bonds_back_counts = libtbx.dict_with_default_0()
    n_roots = 0
    number_of_bonds = flex.size_t([len(bond_list)
      for bond_list in self.bond_lists])
    perm_number_of_bonds = flex.sort_permutation(
      data=number_of_bonds, reverse=True)
    for root_i_seq in perm_number_of_bonds:
      if (serial[root_i_seq] is not None): continue
      n_roots += 1
      curr = []
      next = [root_i_seq]
      serial[root_i_seq] = 0
      i_shell = 0
      while (len(next) != 0):
        i_shell += 1
        prev = curr
        curr = next
        next = []
        for curr_i_seq in curr:
          for bond in self.bond_lists[curr_i_seq]:
            j_seq = bond.j_seq
            if (j_seq in prev): continue
            if (j_seq in curr):
              if (serial[curr_i_seq] < serial[j_seq]):
                self.bonds_back.append([curr_i_seq,j_seq])
                bonds_back_counts[j_seq] += 1
                self.degrees_of_freedom[j_seq] -= 1
                if (show_bond_back):
                  print "bond back:", serial[curr_i_seq],serial[j_seq], \
                    "dof:", self.degrees_of_freedom[j_seq], (curr_i_seq, j_seq)
            else:
              if (j_seq in next):
                self.bonds_back.append([curr_i_seq,j_seq])
                bonds_back_counts[j_seq] += 1
                self.degrees_of_freedom[j_seq] -= 1
                if (show_bond_back):
                  print "bond back:", serial[curr_i_seq],serial[j_seq], \
                    "dof:", self.degrees_of_freedom[j_seq], (curr_i_seq, j_seq)
              else:
                next.append(j_seq)
                self.shell_number[j_seq] = i_shell
                self.bonds_forward.append([curr_i_seq,j_seq])
                serial[j_seq] = len(self.bonds_forward)
                self.degrees_of_freedom[j_seq] -= 1
    self.rigid_ids = [None] * len(atom_list)
    rigid_id = 0
    for root_i_seq in xrange(len(atom_list)):
      if (self.rigid_ids[root_i_seq] is not None): continue
      def assign_rigid_id_to_bonded(i_seq):
        for bond in self.bond_lists[i_seq]:
          if (self.rigid_ids[bond.j_seq] is not None): continue
          if (self.degrees_of_freedom[bond.j_seq] < 1):
            self.rigid_ids[bond.j_seq] = rigid_id
            assign_rigid_id_to_bonded(i_seq=bond.j_seq)
        return True
      if (self.degrees_of_freedom[root_i_seq] < 1):
        assign_rigid_id_to_bonded(i_seq=root_i_seq)
        rigid_id += 1
    bad = []
    for i_seq,count in bonds_back_counts.items():
      if (count > 2):
        bad.append(count)
        self.special_labels.append((i_seq, str(count)))
    if (len(bad) != 0):
      print "bad:", bad
    if (len(atom_list) < 30):
      print "rigid_ids:", self.rigid_ids
    for i_seq in xrange(len(atom_list)):
      if (self.rigid_ids[i_seq] is None):
        r = "*"
      else:
        r = str(self.rigid_ids[i_seq])
      if (1):
        atom_list[i_seq].label = atom_list[i_seq].label.strip()
      else:
        atom_list[i_seq].label = " " + r + " " + str(serial[i_seq]) \
                               + " " + atom_list[i_seq].label.strip() \
                               + " " + str(self.degrees_of_freedom[i_seq]) \
                               + " (%d)"  % self.shell_number[i_seq]
    print "Number of roots:", n_roots
    sdf =  sum(self.degrees_of_freedom)
    print "Sum of degrees of freedom:", sdf, \
      "%.3f" % (sdf / (3 * max(1,len(atom_list))))
    self.check_bonds_accounted_for()
    return None

  def count_edges(self):
    result = sum([len(bond_list) for bond_list in self.bond_lists])
    assert result % 2 == 0
    result //= 2
    return result

  def check_bonds_accounted_for(self):
    n_bonds_total = self.count_edges()
    n_bonds_accounted_for = (len(self.bonds_forward) + len(self.bonds_back))
    if (n_bonds_accounted_for != n_bonds_total):
      print "MISSING BONDS!", n_bonds_accounted_for, n_bonds_total
    else:
      print "All bonds accounted for."

  def construct_rigidity_matrix(self):
    vertices = [a.site for a in self.atom_list]
    n_edges = self.count_edges()
    if (n_edges == 0): return None
    n_vertices = len(vertices)
    n_columns = n_vertices*3
    result = flex.double(flex.grid(n_edges, n_columns), 0)
    i_edge = 0
    for i_seq,j_seq in self.edge_iterator():
      dij = vertices[i_seq] - vertices[j_seq]
      def copy_to_matrix(i_seq, sign):
        i = i_edge * n_columns + i_seq*3
        for x in dij:
          result[i] = sign * x
          i += 1
      copy_to_matrix(i_seq=i_seq, sign= 1)
      copy_to_matrix(i_seq=j_seq, sign=-1)
      i_edge += 1
    assert i_edge == n_edges
    return result

  def construct_integer_rigidity_matrix(self, n_dim):
    edge_list = []
    for i_seq,j_seq in self.edge_iterator():
      edge_list.append((i_seq,j_seq))
    return construct_integer_rigidity_matrix(
      n_dim=n_dim, n_vertices=len(self.atom_list), edge_list=edge_list)

  def construct_symbolic_rigidity_matrix(self):
    n_edges = self.count_edges()
    if (n_edges == 0): return None
    n_vertices = len(self.atom_list)
    n_columns = n_vertices*3
    result = []
    for i_seq,j_seq in self.edge_iterator():
      row = [0] * n_columns
      ev = edge_vector(i_seq, j_seq)
      def copy_to_row(i_seq, sign):
        i = i_seq*3
        for j in xrange(3):
          row[i+j] = sign * ev[j]
      copy_to_row(i_seq=i_seq, sign= 1)
      copy_to_row(i_seq=j_seq, sign=-1)
      result.append(row)
    return result

  def randomize_atom_sites(self):
    al = self.atom_list
    mean_distances = flex.double()
    for i_seq,edge_list in enumerate(self.edge_lists()):
      distances = flex.double()
      for j_seq in edge_list:
        distances.append(abs(al[i_seq].site - al[j_seq].site))
      mean_distances.append(flex.mean_default(distances, 0))
    for a,md in zip(al, mean_distances):
      a.site += matrix.col([(random.random()*2-1)*md*0.2 for i in xrange(3)])

  def add_edges(self, edge_list_list):
    self._edge_lists = None
    for edge_list in edge_list_list:
      for e in edge_list:
        self.add_bond(e)

  def check_edges(self):
    edge_sets = []
    for edge_list in self.edge_lists():
      edge_set = set(edge_list)
      assert len(edge_set) == len(edge_list)
      edge_sets.append(edge_set)
    for i_seq,edge_set in enumerate(edge_sets):
      for j_seq in edge_set:
        assert i_seq in edge_sets[j_seq]

  def as_graph_given_command_line_options(self, co, simplify_large=False):
    return self.as_graph(
      type=co.as_graph,
      show_pie=co.show_pie,
      add_pie=co.add_pie,
      show_bond_bending=co.show_bond_bending,
      add_bond_bending=co.add_bond_bending,
      show_sites_and_edges_and_exit=co.show_sites_and_edges_and_exit,
      find_face_sharing=co.find_face_sharing,
      randomize_sites=not co.no_randomize_sites,
      run_edge_puzzle=co.edge_puzzle,
      build_t_construction=co.t_construction,
      t_construction_fixed_root_i_seq=co.root,
      build_hystraints=co.hystraints,
      simplify_large=simplify_large)

  def as_graph(self,
        type=4,
        show_pie=False,
        add_pie=False,
        show_bond_bending=False,
        add_bond_bending=False,
        show_sites_and_edges_and_exit=False,
        find_face_sharing=False,
        randomize_sites=True,
        run_edge_puzzle=False,
        build_t_construction=True,
        t_construction_fixed_root_i_seq=None,
        build_hystraints=False,
        simplify_large=False):
    self.check_edges()
    if (1):
      for i_seq,atom in enumerate(self.atom_list):
        atom.label = "V%d" % i_seq
    if (0):
      new_edge_lists = rice_rigidity(
        edge_lists=self.edge_lists(),
        pdb_file_name=self.pdb_file_name,
        atom_attributes_list=self.atom_attributes_list)
      if (new_edge_lists is not None):
        print "INFO: using edge_lists from CNS"
        self._edge_lists = None
        self.bond_lists = []
        self.init_bond_lists()
        for i_seq,edge_list in enumerate(new_edge_lists):
          for j_seq in edge_list:
            if (i_seq < j_seq):
              self.add_bond((i_seq,j_seq))
        self.check_edges()
    add_pie_applied = False
    if (show_pie or add_pie or find_face_sharing):
      tverts_list_per_vertex, self.potential_implicit_edges = tetrahedra_hunt(
        edge_lists=self.edge_lists())
      from rigidity_practical import find_hyper_edges
      pie2 = find_hyper_edges(
        n_vertices=len(self.atom_list),
        edge_list=list(self.edge_iterator()),
        max_depth=4)
      print len(self.potential_implicit_edges), len(pie2)
      if (len(self.potential_implicit_edges) != len(pie2)):
        print self.potential_implicit_edges
        print pie2
        print "PIE MISMATCH"
        dof1 = determine_degrees_of_freedom(
          n_dim=3,
          n_vertices=len(self.atom_list),
          edge_list=list(self.edge_iterator())
                   +list(self.potential_implicit_edges),
          method="float")
        print "dof1:", dof1
        dof2 = determine_degrees_of_freedom(
          n_dim=3,
          n_vertices=len(self.atom_list),
          edge_list=list(self.edge_iterator())+pie2,
          method="float")
        print "dof2:", dof2
        assert dof1 == 6
        assert dof2 == 6
      if (1):
        self.potential_implicit_edges = set(pie2)
      if (add_pie):
        if (not simplify_large
            or (    len(self.atom_list) < 30
                and len(self.potential_implicit_edges) < 100)):
          self.add_edges(edge_list_list=[self.potential_implicit_edges])
          self.check_edges()
          add_pie_applied = True
        else:
          print "simplify_large: not adding bond-bending edges"
    if (find_face_sharing):
      find_face_sharing_tetrahedra(
        edge_lists=self.edge_lists(),
        tverts_list_per_vertex=tverts_list_per_vertex)
    if ((show_bond_bending or add_bond_bending) and not add_pie):
      self.secondary_graphs = construct_secondary_graphs(
        edge_set=set(self.edge_iterator()),
        edge_lists=self.edge_lists())
      if (add_bond_bending):
        if (not simplify_large
            or (    len(self.atom_list) < 30
                and sum([len(g) for g in self.secondary_graphs]) < 100)):
          self.add_edges(edge_list_list=self.secondary_graphs)
          self.check_edges()
        else:
          print "simplify_large: not adding bond-bending edges"
    if (show_sites_and_edges_and_exit):
      for atom in self.atom_list:
        print "("+",".join(tuple(["%.6g" % v for v in atom.site]))+"),"
      for e in self.edge_iterator():
        print "(%d,%d)," % e,
      print
      return
    if (randomize_sites):
      self.randomize_atom_sites()
    if (0):
      cluster_construction(
        edge_list=list(self.edge_iterator()),
        edge_lists=self.edge_lists())
    if (build_t_construction):
      distances = self.extract_distances()
      t_const = t_construction(
        edge_lists=self.edge_lists(),
        distances=distances,
        fixed_root_i_seq=t_construction_fixed_root_i_seq,
        sites=[a.site for a in self.atom_list])
      self.hinges = t_const.hinges
    else:
      t_const = None
    if (build_hystraints):
      import hystraints
      redundant_edge_sets = [set(edge_list) for edge_list in self.edge_lists()]
      point_placement_order = hystraints.find_point_placement_order(
        redundant_edge_sets=redundant_edge_sets)
      for triangle_loops_only in [False, True]:
        t_parameterization = hystraints.make_t_parameterization(
          point_placement_order=point_placement_order,
          sites=[a.site for a in self.atom_list],
          triangle_loops_only=triangle_loops_only)
        nr = t_parameterization.n_restrained
        if (nr != 0):
          print "Number of restraints triangle_loops_only=%s: %d" % (
            triangle_loops_only, nr)
    if (0):
      cycle_enumeration(
        n_vertices=len(self.atom_list), bond_lists=self.bond_lists)
    if (len(self.atom_list) < 100):
      rigidity_matrix = self.construct_rigidity_matrix()
      if (rigidity_matrix is not None):
        import tntbx
        svd = tntbx.svd(m=rigidity_matrix)
        svd_rank = svd.rank()
        n_redundant_edges = svd.n_rows - svd_rank
        print "rank of rigidity matrix:", svd_rank, "of", svd.n_rows,
        if (n_redundant_edges != 0):
          print "deficient", n_redundant_edges,
        print
        svd_dof = 3 * len(self.atom_list) - svd_rank
        print "rigidity-matrix derived dof:", svd_dof
        if (add_pie_applied and randomize_sites):
          if (len(self.atom_list) == 1):
            assert svd_dof == 3
          elif (len(self.atom_list) == 2):
            assert svd_dof == 5
          else:
            assert svd_dof == 6
      if (    rigidity_matrix is not None
          and (not simplify_large or len(self.atom_list) < 50)):
        n_dim = 3
        if (0):
          symbolic_rigidity_matrix = self.construct_symbolic_rigidity_matrix()
        else:
          if (0):
            n_dim = 2
          symbolic_rigidity_matrix = self.construct_integer_rigidity_matrix(
            n_dim=n_dim)
        if (0): # for debugging the row-echelon implementation
          m = symbolic_rigidity_matrix
          i = 0
          for r in m:
            for j in xrange(len(r)):
              r[j] = rigidity_matrix[i]
              i += 1
        def show_srm():
          for row in symbolic_rigidity_matrix:
            s = []
            for v in row:
              if (isinstance(v, float)):
                s.append("%.6g" % round(v,6))
              else:
                s.append(str(v))
            print " ".join(s)
        if (0):
          print "before row echelon:"
          show_srm()
        pivot_values, free_vars = srm_row_echelon_form(
          m=symbolic_rigidity_matrix)
        if (0):
          print "after row echelon:"
          show_srm()
          print "free_vars:", free_vars
        print "min pivot:", min([abs(v) for v in pivot_values])
        srm_rank = len(symbolic_rigidity_matrix[0]) - len(free_vars)
        print "srm_rank:", srm_rank
        print "srm dofs:", len(free_vars)
        if (n_dim == 3):
          if (not randomize_sites):
            assert srm_rank >= svd_rank
          else:
            assert srm_rank == svd_rank
            if (t_const is not None and t_const.n_dof is not None):
              n = t_const.n_dof + 6 - t_const.p_dof + n_redundant_edges
              print "compare:", len(free_vars), n
              assert len(free_vars) == n
              if (t_const.fixed_downstream is not None):
                sumf = sum(t_const.fixed_downstream.values())
                assert t_const.n_dof >= sumf
                if (t_const.n_dof - sumf > svd_dof - 6):
                  print "t_const INSUFFICIENT n_dof - sumf > svd_dof - 6:" \
                    " %d - %d = %d > %d" % (
                      t_const.n_dof, sumf, t_const.n_dof - sumf, svd_dof - 6)
              assert len(t_const.invariant_edges) <= n_redundant_edges
              if (len(t_const.invariant_edges) < n_redundant_edges):
                print "t_const INSUFFICIENT invariant edges:", \
                  len(t_const.invariant_edges), n_redundant_edges
          if (svd_dof == 6 and run_edge_puzzle):
            edge_puzzle(edge_lists=self.edge_lists())
        elif (n_dim < 3):
          assert srm_rank <= svd_rank
        else:
          assert srm_rank >= svd_rank
    return getattr(self, "as_graph%d" % type)()

def edge_iterator(edge_lists):
  for i,edge_list in enumerate(edge_lists):
    for j in edge_list:
      if (j < i): continue
      yield (i, j)

def edge_puzzle(edge_lists):
  edge_list = list(edge_iterator(edge_lists=edge_lists))
  n_vertices = len(edge_lists)
  dof = determine_degrees_of_freedom(
    n_dim=3, n_vertices=n_vertices, edge_list=edge_list)
  assert dof == 6
  #
  # enumerate alternative edges (those not in edge_lists)
  all_i = set(range(n_vertices))
  alt_list = []
  for i,el in enumerate(edge_lists):
    for j in all_i.difference(el):
      if (j == i): continue
      if (j < i): continue
      alt_list.append((i,j))
  #
  n_rigid = 0
  n_skipped = 0
  n_floppy = 0
  for iel in xrange(len(edge_list)):
    orig_edge = edge_list[iel]
    oi,oj = orig_edge
    edge_counts_oi = len(edge_lists[oi])
    edge_counts_oj = len(edge_lists[oj])
    for alt_edge in alt_list:
      ai,aj = alt_edge
      predicted_as_floppy = False
      if (   (edge_counts_oi == 3 and ai != oi and aj != oi)
          or (edge_counts_oj == 3 and ai != oj and aj != oj)):
        predicted_as_floppy = True
      edge_list[iel] = alt_edge
      dof = determine_degrees_of_freedom(
        n_dim=3, n_vertices=n_vertices, edge_list=edge_list)
      assert dof >= 6
      if (dof == 6):
        assert not predicted_as_floppy
        n_rigid += 1
      else:
        if (predicted_as_floppy):
          n_skipped += 1
        else:
          n_floppy += 1
          print "floppy: -(%d,%d)" % orig_edge + "+(%d,%d)" % alt_edge
    edge_list[iel] = orig_edge
  print "n_rigid:", n_rigid
  print "n_skipped:", n_skipped
  print "n_floppy:", n_floppy
  n_rsf = n_rigid + n_skipped + n_floppy
  print "n_rigid+n_skipped+n_floppy:", n_rsf
  n_possible_edges = n_vertices * (n_vertices-1) // 2
  if (n_vertices < 2):
    min_n_edges_to_achieve_rigidity = 0
  elif (n_vertices == 2):
    min_n_edges_to_achieve_rigidity = 1
  else:
    min_n_edges_to_achieve_rigidity = (n_vertices - 2) * 3
  predicted_n_rsf = (n_possible_edges - min_n_edges_to_achieve_rigidity) \
    * min_n_edges_to_achieve_rigidity
  assert predicted_n_rsf == n_rsf

def make_edge_lists(n_vertices, edge_list):
  result = []
  for i in xrange(n_vertices):
    result.append([])
  for i,j in edge_list:
    result[i].append(j)
    result[j].append(i)
  return result

def connected_clusters(edge_lists):
  result = []
  n_vertices = len(edge_lists)
  done = [False] * n_vertices
  for root_i_seq in xrange(n_vertices):
    if (done[root_i_seq]): continue
    cluster = []
    def traverse(i_seq):
      cluster.append(i_seq)
      done[i_seq] = True
      for j_seq in edge_lists[i_seq]:
        if (done[j_seq]): continue
        traverse(i_seq=j_seq)
    traverse(i_seq=root_i_seq)
    result.append(cluster)
  return result

def random_graphs(n_vertices=12, n_trials=1000, edge_likelihood=0.5):
  mt = flex.mersenne_twister(seed=0)
  max_edges = (n_vertices * (n_vertices - 1)) // 2
  for i_trial in xrange(n_trials):
    flags = mt.random_bool(size=max_edges, threshold=edge_likelihood)
    f = iter(flags)
    edge_list = []
    n_free_edges = 0
    for i in xrange(n_vertices-1):
      for j in xrange(i+1,n_vertices):
        if (f.next()):
          edge_list.append((i,j))
        else:
          n_free_edges += 1
    assert len(edge_list) + n_free_edges == max_edges
    #
    clusters = connected_clusters(
      edge_lists=make_edge_lists(n_vertices=n_vertices, edge_list=edge_list))
    if (len(clusters) != 1):
      for i in xrange(len(clusters)-1):
        edge_list.append((clusters[i][0], clusters[i+1][0]))
      clusters = connected_clusters(
        edge_lists=make_edge_lists(n_vertices=n_vertices, edge_list=edge_list))
      assert len(clusters) == 1
    #
    if (0):
      print "edge_list:", edge_list
      sys.stdout.flush()
    m = construct_integer_rigidity_matrix(
      n_dim=3, n_vertices=n_vertices, edge_list=edge_list)
    pivot_values, free_vars = srm_row_echelon_form(m=m)
    rank = len(m[0]) - len(free_vars)
    n_redundant_edges = len(edge_list) - rank
    print "rank of rigidity matrix:", rank, "of", len(m[0]),
    if (n_redundant_edges != 0):
      print "deficient", n_redundant_edges
    print
    #
    edge_lists = make_edge_lists(n_vertices=n_vertices, edge_list=edge_list)
    distances = []
    for i in xrange(n_vertices):
      distances.append({})
    for i,j in edge_list:
      distances[i][j] = 1
    t_const = t_construction(
      edge_lists=edge_lists, distances=distances)
    if (t_const is not None and t_const.n_dof is not None):
      n = t_const.n_dof + 6 - t_const.p_dof + n_redundant_edges
      print "compare:", len(free_vars), n
      assert len(free_vars) == n
    #
    if (1):
      cluster_construction(edge_list, edge_lists=edge_lists)

def process_command_line_args(args):
  return (libtbx_option_parser(
    usage="python msd_as_graph.py"
         +" [options] code")
    .option(None, "--tab_stop",
      action="store_true",
      default=False)
    .option(None, "--practical",
      action="store_true",
      default=False)
    .option(None, "--dynamics",
      action="store_true",
      default=False)
    .option(None, "--interleaved_minimization_steps",
      action="store",
      type="int",
      default=3,
      metavar="INT")
    .option(None, "--as_graph",
      action="store",
      type="int",
      default=4,
      metavar="INT")
    .option(None, "--attach_inverse",
      action="append",
      type="int",
      default=[],
      metavar="INT")
    .option(None, "--delete",
      action="append",
      type="str",
      default=[],
      metavar="INDICES")
    .option(None, "--add_edge",
      action="append",
      type="str",
      default=[],
      metavar="(j,i)")
    .option(None, "--show_pie",
      action="store_true",
      default=False)
    .option(None, "--add_pie",
      action="store_true",
      default=False)
    .option(None, "--show_bond_bending",
      action="store_true",
      default=False)
    .option(None, "--add_bond_bending",
      action="store_true",
      default=False)
    .option(None, "--show_sites_and_edges_and_exit",
      action="store_true",
      default=False)
    .option(None, "--find_face_sharing",
      action="store_true",
      default=False)
    .option(None, "--no_randomize_sites",
      action="store_true",
      default=False)
    .option(None, "--edge_puzzle",
      action="store_true",
      default=False)
    .option(None, "--root",
      action="store",
      type="int",
      default=None,
      metavar="INT")
    .option(None, "--t_construction",
      action="store_true",
      default=False)
    .option(None, "--hystraints",
      action="store_true",
      default=False)
  ).process(args=args)

lib_codes = [
  "triangle",
  "sqtri",
  "cube",
  "cube_oct",
  "p120",
  "tet",
  "tet-(2,3)",
  "tet-(2,3)-(0,2)",
  "tet-(2,3)-(0,1)",
  "tet-(2,3)-(0,2)-(0,3)",
  "tet-(2,3)-(0,1)-(0,3)",
  "oct",
  "rho",
  "dod",
  "tri",
  "ico",
  "ico1",
  "bucky",
  "soct",
  "toct",
  "gyro",
  #"t7-(0,1)+(4,5)-(0,3)+(5,6)", # XXX find out what happened to this
  "chain1",
  "chain2",
  "chain3",
  "chain4",
  "chain5",
  "loop3",
  "loop4",
  "loop5",
  "prism3",
  "prism4",
  "prism5",
  "prism6",
  "fan3",
  "fan4",
  "fan5",
  "shell3",
  "shell4",
  "shell5",
  "pivot3",
  "pivot4",
  "pivot5",
  "barrel3",
  "barrel4",
  "barrel5",
  "barrel6",
  "bcyc2",
  "bcyc3",
  "bcyc4",
  "bcyc5",
  "mt1996",
  "ico:1",
  "special1",
  "special2"]

def run(args):
  command_line = process_command_line_args(args=args)
  args = command_line.args
  co = command_line.options
  if (len(args) == 0):
    assert dir_pickles is not None
    for node in os.listdir(dir_pickles):
      if (not node.startswith("elbow.")): continue
      if (not node.endswith(".pickle")): continue
      args.append(node[6:-7])
  elif (args == ["lib"]):
    args = lib_codes
  if (args == ["random"]):
    random_graphs()
    return
  for code in args:
    comp = process(
      code=code,
      attach_inverse_pivots=co.attach_inverse,
      delete_expressions=co.delete,
      add_edge_expressions=co.add_edge)
    if (co.practical):
      rigidity_practical.rigidity_analysis(
        n_vertices=len(comp.atom_list),
        edge_list=list(comp.edge_iterator()),
        add_bond_bending=co.add_bond_bending)
    if (co.dynamics):
      import dynamics_prototype
      dynamics_prototype.run(comp=comp)
    else:
      try:
        comp.as_graph_given_command_line_options(
          co=co, simplify_large=args is lib_codes)
        print
      except KeyboardInterrupt: raise
      except Exception:
        raise
        print "ERROR code", code
        print "*"*79
        sys.stdout.write(traceback.format_exc())
        print "*"*79
        print
    sys.stdout.flush()
  print format_cpu_times()
  sys.stdout.flush()

if __name__=="__main__":
  run(sys.argv[1:])
