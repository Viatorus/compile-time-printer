import sys

if sys.version_info[:2] >= (3, 8):
    # TODO: Import directly (no need for conditional) when `python_requires = >= 3.8`
    from importlib.metadata import PackageNotFoundError, version  # pragma: no cover
else:
    from importlib_metadata import PackageNotFoundError, version  # pragma: no cover

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = 'compile-time-printer'
    __version__ = version(dist_name)
except PackageNotFoundError:
    __version__ = 'unknown'  # pragma: no cover
finally:
    del version, PackageNotFoundError
