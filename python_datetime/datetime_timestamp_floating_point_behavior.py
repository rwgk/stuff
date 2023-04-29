"""Show datetime.datetime.timestamp() floating-point behavior.

Please review the output of this code first, then look back here.

* https://docs.python.org/3/library/datetime.html
* https://en.wikipedia.org/wiki/IEEE_754
"""

import datetime
import sys


def annotate_behavior(t_int, t_flt):
    if int(t_flt) == t_int:
        return "truncating"
    if int(t_flt) == t_int + 1:
        return "ROUNDING UP"
    return "LOSSY"


def dt_strftime(dt):
    return ("000" + dt.strftime("%Y-%m-%d %H:%M:%S.%f"))[-26:]


def run(args):
    """Please review the output of this code first, then look back here."""

    assert len(args) == 1, "sample_max_exponent (e.g. 53 for IEEE 754)"

    sample_max_exponent = int(args[0])

    resolution_exponent = 6
    resolution_num = 10**resolution_exponent  # 1000000
    resolution_nines = resolution_num - 1  # 999999
    resolution_nines_over_num = resolution_nines / resolution_num  # 0.999999

    tz_utc = datetime.timezone.utc
    dt_min = datetime.datetime.min.replace(tzinfo=tz_utc)
    dt_max = datetime.datetime.max.replace(tzinfo=tz_utc)
    dt_min_t = dt_min.timestamp()
    dt_max_t = dt_max.timestamp()

    print("datetime.min.timestamp()", dt_min_t, "", dt_strftime(dt_min))
    print("datetime.max.timestamp()", dt_max_t, "", dt_strftime(dt_max))
    print()

    print("              offset          t_int   t_int+0.999999")

    def print_mm(name, t, offset):
        t_int = int(t) + offset
        t_flt = t_int + resolution_nines_over_num
        print(
            f"{name}  {offset:6}  {t_int:13}  {t_flt:15}"
            f"  {annotate_behavior(t_int, t_flt)}"
        )

    for offset in (0, 1):
        print_mm("datetime.min", dt_min_t, offset)
    for offset in (-1, 0):
        print_mm("datetime.max", dt_max_t, offset)
    print()

    print("2**e  offset             t_int        t_int+0.999999")
    t_int_done = set()
    for exponent in range(sample_max_exponent + 1):
        ip2 = 2**exponent
        for offset in (-1, 0, 1):
            t_int = ip2 + offset
            if t_int in t_int_done:
                continue
            t_int_done.add(t_int)
            t_flt = t_int + resolution_nines_over_num
            if t_flt < dt_max_t:
                dt_utc = datetime.datetime.fromtimestamp(t_int, tz=tz_utc)
                dt_fmt = dt_strftime(dt_utc)
            else:
                dt_fmt = "out of datetime range"
            print(
                f"{exponent:4}  {offset:6}  {t_int:16}  {t_flt:20}"
                f"  {annotate_behavior(t_int, t_flt):11}  {dt_fmt}"
            )
    print()


if __name__ == "__main__":
    run(args=sys.argv[1:])
