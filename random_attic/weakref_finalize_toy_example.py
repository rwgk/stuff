import weakref

class ShopKeeper:
    __slots__ = ("__weakref__", "serno", "exception_harness")

    def __init__(self, serno, exception_harness):
        self.serno = serno
        self.exception_harness = exception_harness
        weakref.finalize(self, self.close)

    def close(self):
        if self.exception_harness:
            try:
                print("close", self.serno, 1 / (self.serno - 2))
            except Exception:
                print("problem", self.serno)
        else:
                print("close", self.serno, 1 / (self.serno - 2))

for exception_harness in [False, True]:
    for serno in range(5):
        ShopKeeper(serno, exception_harness)
