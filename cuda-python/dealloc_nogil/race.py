import os, threading, time, repro

# Make allocator catch double-frees loudly (CPython 3.8+ honors this)
os.environ.setdefault("PYTHONMALLOC", "debug")

def run_once(make_twins):
    a, b = make_twins(64 * 1024)
    barrier = threading.Barrier(2)

    def worker(x):
        barrier.wait()
        # Drop the last reference in this thread; __dealloc__ runs here.
        del x
        # Keep thread alive briefly so both destructors overlap
        time.sleep(0.02)

    t1 = threading.Thread(target=worker, args=(a,))
    t2 = threading.Thread(target=worker, args=(b,))
    t1.start(); t2.start()

    # Ensure the threads are the sole owners
    del a, b

    t1.join(); t2.join()

if __name__ == "__main__":
    repro.start_driver()
    try:
        # With GIL released in __dealloc__ (WrapperNogil), this tends to abort
        # with "double free or corruption", or segfault, within a few to a few thousand iterations.
        for i in range(1, 1_000_000):
            if i % 1000 == 0:
                print("iteration", i)
            run_once(repro.make_twins_nogil)

        # If you switch to the GIL-held variant below, it should run indefinitely:
        # for i in range(1, 1_000_000):
        #     run_once(repro.make_twins_with_gil)
    finally:
        repro.stop_driver()
