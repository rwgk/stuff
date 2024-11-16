import weakref


class ShopKeeper:
    class _Members:
        __slots__ = ("serno", "exception_harness")

        def __init__(self, serno, exception_harness):
            self.serno = serno
            self.exception_harness = exception_harness

        def close(self):
            if self.exception_harness:
                try:
                    print("        Close", self.serno, 1 / (self.serno - 1))
                except Exception:
                    print("        PROBLEM", self.serno)
            else:
                print("        Close", self.serno, 1 / (self.serno - 1))

    __slots__ = ("__weakref__", "_members")

    def __init__(self, serno, exception_harness):
        self._members = ShopKeeper._Members(serno, exception_harness)
        weakref.finalize(self, self._members.close)


def short_term_shop_keeper(serno, exception_harness):
    print("    Start short term", serno, exception_harness)
    ShopKeeper(serno, exception_harness)
    print("    End short term")


def experiment():
    print("Start experiment")
    for exception_harness in [False, True]:
        for serno in range(3):
            short_term_shop_keeper(serno, exception_harness)
    print("End experiment")


if __name__ == "__main__":
    experiment()
    print("All done.")
