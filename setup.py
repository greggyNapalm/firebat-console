#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

#if not hasattr(sys, 'version_info') or sys.version_info < (2, 6, 0, 'final'):
#    raise SystemExit("Firebat requires Python 2.7 or later.")

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
    #'numpy',
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
        "bin/fire-chart",
    ],
    packages=[
        'firebat',
        'firebat.console',
    ],
    package_data={
        "firebat": [
            "console/defaults.yaml",
            "console/phantom.conf.jinja",
            "result_markdown/js/firebat/*.js",
            "result_markdown/js/*.js",
            "result_markdown/img/*.png",
            "result_markdown/img/*.ico",
            "result_markdown/css/*.css",
            "result_markdown/less/*.less",
            "result_markdown/less/*.less",
            "result_markdown/*.jinja",
            ],
        },
    zip_safe=False,
    install_requires=install_requirements,
    tests_require=['nose'],
    test_suite='nose.collector',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        "Topic :: Software Development :: Testing :: Traffic Generation",
    ],
)
