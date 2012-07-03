#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
firebat.test.base
~~~~~~~~~~~~~~~~~

Common function for project unittests.
"""

import os
import sys
import datetime
import argparse
import logging
import getpass
import cPickle
import time
import commands
import copy
import base64
from string import maketrans
from progressbar import Bar, ProgressBar, Percentage, ETA

import yaml
import simplejson as json

def get_fire_dict(name='valid'):
    file_path = os.path.dirname(__file__) + '/fixtures//fire_%s.json' % name
    try:
        with open(file_path, 'r') as fh:
            fire_json = fh.read()
    except IOError, e:
        __msg = 'Can\'t open fire fixture: %s' % e
        return False
    return  json.loads(fire_json) 


if __name__ == '__main__':
    print get_fire_dict()
