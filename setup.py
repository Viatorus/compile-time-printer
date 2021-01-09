"""
    Setup file for compile-time-printer.
    Use setup.cfg to configure your project.

    This file was generated with PyScaffold 4.0b1.
    PyScaffold helps you to put up the scaffold of your new Python project.
    Learn more under: https://pyscaffold.org/
"""
import os

from setuptools import setup

if __name__ == '__main__':
    try:
        os.symlink('../../include', 'src/compile_time_printer/include')
        setup(use_scm_version={'version_scheme': 'post-release'})
    except:  # noqa
        print(
            '\n\nAn error occurred while building the project, '
            'please ensure you have the most updated version of setuptools, '
            'setuptools_scm and wheel with:\n'
            '   pip install -U setuptools setuptools_scm wheel\n\n'
        )
        raise
    finally:
        os.unlink('src/compile_time_printer/include')
