
from setuptools import setup, Extension
from Cython.Build import cythonize

exts = [Extension("event_demo", ["event_demo.pyx"])]

setup(
    name="event_demo",
    ext_modules=cythonize(
        exts,
        language_level=3,
        annotate=True,   # writes event_demo.html to inspect C/Python crossings
        force=True,      # forces regeneration even if nothing changed
    ),
)
