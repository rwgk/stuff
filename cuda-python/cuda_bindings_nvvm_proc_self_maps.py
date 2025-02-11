import difflib
import sys

print(f"{sys.path=}", flush=True)
print()

stages = []


def get_proc_self_maps_paths():
    paths = set()
    with open("/proc/self/maps") as f:
        for line in f:
            parts = line.strip().split(maxsplit=5)
            if len(parts) == 6:
                path = parts[5]
                if path.startswith("/"):
                    paths.add(path)
    return "\n".join(sorted(paths)) + "\n"


def fetch_proc_self_maps(label):
    stages.append((label, get_proc_self_maps_paths()))


fetch_proc_self_maps("fresh")
import cuda
fetch_proc_self_maps("after import cuda")
import cuda.bindings
fetch_proc_self_maps("after import cuda.bindings")
import cuda.bindings.nvvm
fetch_proc_self_maps("after import cuda.bindings.nvvm")
try:
    cuda.bindings.nvvm.version()
except:
    status = "failure"
else:
    status = "success"
fetch_proc_self_maps(f"after cuda.bindings.nvvm.version() {status}")

for a, b in zip(stages[:-1], stages[1:]):
    print("label:", b[0])
    if a[1] == b[1]:
        print("NO DIFF")
    else:
        diff = difflib.unified_diff(
            a[1].splitlines(),
            b[1].splitlines(),
            fromfile="before",
            tofile="after",
            lineterm="",
        )
        print("\n".join(diff))
    print()
    print()
