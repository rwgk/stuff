from __future__ import division

from cctbx import sgtbx


def run():
  all_flds = set()
  for symbols in sgtbx.space_group_symbol_iterator():
    symbol = symbols.universal_hermann_mauguin()
    print symbol
    flds = symbol.split()
    all_flds.update(flds)
  with open('symops_530_html_markup.py', 'w') as f:
    print >> f, 'html_markup = {'
    for fld in sorted(all_flds):
      print >> f, "    '%s': '%s'," % (fld, fld)
    print >> f, '}'


if __name__ == '__main__':
  run()
