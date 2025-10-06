from setuptools import setup, Extension
from Cython.Build import cythonize

ext = Extension(
    "repro",
    sources=["repro.pyx", "mockcuda.c"],
)

setup(
    name="repro",
    ext_modules=cythonize([ext], language_level=3),
)
