from __future__ import division

from cctbx import sgtbx
import symops_530_html_markup_cb


def html_markup(symbol):
  return [symops_530_html_markup_cb.html_markup[plain]
          for plain in symbol.split()]


def run():
  for symbols in sgtbx.space_group_symbol_iterator():
    hm = html_markup(symbols.hermann_mauguin())
    ext = symbols.extension()
    if ext == '\0': ext = ''
    uhm = html_markup(symbols.universal_hermann_mauguin())
    print '%s,%s,%s,%s' % (symbols.number(), ''.join(hm), ext, ' '.join(uhm))


if __name__ == '__main__':
  run()
