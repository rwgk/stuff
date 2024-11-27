import weakref


class ShopKeeper:
    class _MembersNeededForFinalize:
        __slots__ = ("serno", "exception_harness")

        def __init__(self, shop_keeper_obj, serno, exception_harness):
            self.serno = serno
            self.exception_harness = exception_harness
            weakref.finalize(shop_keeper_obj, self.close)

        def close(self):
            if self.exception_harness:
                try:
                    print("        Close", self.serno, 1 / (self.serno - 1))
                except Exception:
                    print("        PROBLEM", self.serno)
            else:
                print("        Close", self.serno, 1 / (self.serno - 1))

    __slots__ = ("__weakref__", "_mnff")

    def __init__(self, serno, exception_harness):
        self._mnff = ShopKeeper._MembersNeededForFinalize(
            self, serno, exception_harness
        )


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
