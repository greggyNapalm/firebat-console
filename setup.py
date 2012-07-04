#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

if not hasattr(sys, 'version_info') or sys.version_info < (2, 7, 0, 'final'):
    raise SystemExit("Firebat requires Python 2.7 or later.")

try:
        from setuptools import setup
except ImportError:
        from distutils.core import setup

from firebat import __version__

install_requirements = [
    'PyYAML',
    'jinja2',
    'progressbar',
    'simplejson',
]

with open("README.rst") as f:
    README = f.read()

with open("docs/changelog.rst") as f:
    CHANGES = f.read()

setup(
    name='firebat-console',
    version=__version__,
    author='Gregory Komissarov',
    author_email='gregory.komissarov@gmail.com',
    description='Console helpers for Phantom load tool',
    long_description=README + '\n' + CHANGES,
    license='BSD',
    url='https://github.com/greggyNapalm/firebat_console',
    keywords=['phantom', 'firebat'],
    scripts=[
        "bin/fire",
        "bin/daemon_fire",
    ],
    packages=[
        'firebat',
        'firebat.console',
    ],
    zip_safe=False,
    install_requires=install_requirements,
    tests_require=['nose'],
    test_suite='nose.collector',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Framework :: Firebat',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.7',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
)
