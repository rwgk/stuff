#pragma once

#if defined(_MSC_VER)
#define SOMELIB_NOINLINE __declspec(noinline)
#else
#define SOMELIB_NOINLINE __attribute__((noinline))
#endif

int somenumber();

SOMELIB_NOINLINE inline int somenumber() { return 13; }
