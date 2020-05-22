"""Produces CSV lists of Count, Author for 1. merge, 2. regular commits.

Usage:
  cd <gitrepo>
  git log -p -m > git_log_p_m_output.txt
  python3 mine_git_log.py git_log_p_m_output.txt
"""

import collections
import sys


class CommitInfo:

  __slots__ = (
      'commit', 'merge', 'author', 'date',
      'author_name')

  def __init__(self):
    for slot in self.__slots__:
      setattr(self, slot, None)


def set_derived_info_in_place(all_commit_info):
  # pylint: disable=missing-docstring
  email_list_by_name = collections.defaultdict(set)
  author_name_buffer = []
  for commit_info in all_commit_info:
    author_line = commit_info.author
    flds = author_line.split('<', 1)
    assert len(flds) == 2, author_line
    assert flds[1].endswith('>'), author_line
    author_name = flds[0].strip()
    email = flds[1][:-1]
    email_list_by_name[author_name].add(email)
    author_name_buffer.append(author_name)
  for commit_info, author_name in zip(all_commit_info, author_name_buffer):
    commit_info.author_name = author_name
  return email_list_by_name


def sorted_by_counts(key_count_items, counts_top_down=True):
  csign = -1 if counts_top_down else 1
  return tuple(
      [(csign * scount, key) for scount, key in sorted(
          [(csign * count, key) for key, count in key_count_items])])


def author_counts(all_commit_info, merge_commit_selector):
  assert isinstance(merge_commit_selector, bool)
  counts_by_author = collections.defaultdict(int)
  for commit_info in all_commit_info:
    if bool(commit_info.merge) is merge_commit_selector:
      counts_by_author[commit_info.author_name] += 1
  return sorted_by_counts(counts_by_author.items())


def run(args):
  # pylint: disable=missing-docstring
  assert len(args) == 1, 'git log -p -m output'
  all_commit_info = []
  full_log_lines = open(args[0]).read().splitlines()
  line_iter = iter(full_log_lines)
  open_block = False
  for line in line_iter:
    if line.startswith('commit '):
      commit_info = CommitInfo()
      assert not open_block
      open_block = True
      for block_line in line_iter:
        if not block_line.strip():
          break
        flds = block_line.split(' ', 1)
        assert len(flds) == 2, block_line
        key = flds[0].lower()
        if key.endswith(':'):
          key = key[:-1]
        if not hasattr(commit_info, key):
          raise RuntimeError('Unexpected line after "commit": %s' % block_line)
        setattr(commit_info, key, flds[1])
      open_block = False
      all_commit_info.append(commit_info)
  assert not open_block
  set_derived_info_in_place(all_commit_info)
  for commit_kind in ['Merge ', '']:
    counts_by_author_name = author_counts(
        all_commit_info, merge_commit_selector=(commit_kind == 'Merge '))
    print('"Count","%sAuthor"' % commit_kind)
    for count, author_name in counts_by_author_name:
      print('%s,%s' % (count, author_name))
    print(',')


if __name__ == '__main__':
  run(args=sys.argv[1:])
