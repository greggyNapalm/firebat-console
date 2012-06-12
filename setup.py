#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os

try:
        from setuptools import setup
except ImportError:
        from distutils.core import setup

setup(
    name='firebat-console',
    version='0.0.1',
    author='Gregory Komissarov',
    author_email='gregory.komissarov@gmail.com',
    description='Console helpers for Phantom load tool',
    license='BSD',
    url='https://github.com/greggyNapalm/firebat_console',
    keywords=['phantom', 'firebat'],
    scripts=["bin/fire"],
    packages=[
        'firebat',
        'firebat.console',
    ],
    zip_safe=False,
    install_requires=[
        'jinja2',
        'progressbar',
    ],
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
