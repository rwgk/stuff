from __future__ import division

from cctbx import sgtbx
import symops_530_html_markup_cb


def run():
  for symbols in sgtbx.space_group_symbol_iterator():
    symbol = symbols.universal_hermann_mauguin()
    html = [
        symops_530_html_markup_cb.html_markup[plain]
        for plain in symbol.split()]
    print ' '.join(html), ' #', symbols.number()


if __name__ == '__main__':
  run()
