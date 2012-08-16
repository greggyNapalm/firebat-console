# -*- coding: utf-8 -*-

"""
firebat.helpers
~~~~~~~~~~~~~~~

A set of functions and tools to help in routine
"""

import os
import sys
import time
import socket
import logging
import commands
import getpass
from pwd import getpwuid
import pprint
pp = pprint.PrettyPrinter(indent=4)

import validictory
import requests


def exit_err(msg):
    '''On critical error, write out msg and exit.
    Args:
        msg: str or list.
    '''
    logger = logging.getLogger('root')
    if isinstance(msg, basestring):
        msg = [msg, ]
    for m in msg:
        logger.error(m)
    if not logger.handlers:
        sys.stderr.write(msg)
    sys.exit(1)


def get_wd_by_pid(pid):
    '''Return POSIX process working directory'''
    cmd = 'readlink -e /proc/%s/cwd' % pid
    status, stdout = commands.getstatusoutput(cmd)
    if status == 0:
        return stdout
    return None


def get_logger(log_path=None, stream=True, is_debug=False):
    '''Return logger obj.
    '''
    logger = logging.getLogger('root')
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s  %(message)s')

    hadlers = []
    if log_path:
        hadlers.append(logging.FileHandler(log_path))

    if stream:
        hadlers.append(logging.StreamHandler())

    if is_debug:
        lvl = logging.DEBUG
    else:
        lvl = logging.INFO

    for h in hadlers:
        h.setLevel(lvl)
        h.setFormatter(formatter)
        logger.addHandler(h)
    return logger

fire_cfg_schema = {
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'addr': {'type': 'string'},
        'input_format': {'type': 'string'},
        'input_file': {'type': 'string'},
        'network_proto': {'type': 'string'},
        'transport_proto': {'type': 'string'},
        'instances': {'type': 'integer'},
        'loop_ammo': {'type': 'boolean'},
        'tag': {
            'items': {
                'type': 'string',
            },
        },
        'time_periods': {
            'items': {
                'type': ['string', 'integer'],
            },
        },
        'load': {
            'items': {
                'type': 'array',
            },
        },
    },
}

test_cfg_schema = {
    'type': 'object',
    'properties': {
        'title': {
            'type': 'object',
            'properties': {
                'task': {'type': 'string'},
                'test_name': {'type': 'string'},
                'test_dsc': {'type': 'string', 'required': False},
            }
        },
        'fire': {
            'items': {
                'type': fire_cfg_schema,
            },
        },
    },
}


def validate(sample, tgt='test'):
    ''' Check test dict structure: required keys and their types.
    Args:
        sample: dict, data to validate.
        tgt: str, part of fb input data(whole test or fire only).

    Returns:
        Raise exception on invalid sample.
    '''
    assert tgt in ['test', 'fire']

    if tgt == 'test':
        validictory.validate(sample, test_cfg_schema)
    elif tgt == 'fire':
        validictory.validate(sample, fire_cfg_schema)

    return True


def test_cfg_complete(test_cfg):
    '''Add some fire_cfg attributes, on first API call'''
    test_cfg['src_host'] = socket.getfqdn()
    test_cfg['uid'] = getpass.getuser()
    return test_cfg

def get_test_uniq_name(test_cfg):
    '''If We got ID from API side - returns ID, else
       generate uniq string with TASK, UID adn TIME.'''
    test_id = test_cfg.get('id', None)
    if test_id:
        name =  test_id
    else:
        name = test_cfg['title']['task'] + '_'
        name += getpass.getuser() + '_'
        name += time.strftime('%Y%m%d-%H%M%S')
    return name

def owner_by_path(path):
    return getpwuid(os.stat(path).st_uid).pw_name

def check_test_lock(locks_path):
    is_busy = False
    locks = []
    for f in os.listdir(locks_path):
        if (f.startswith('lunapark_') or f.startswith('firebat_')) and\
           f.endswith('.lock'):
            f_path = '%s/%s' % (locks_path, f)
            print f_path
            is_busy = True
            locks.append({
                'file_name': f,
                'created_at': os.path.getmtime(f_path),
                'owner': owner_by_path(f_path),
            })
    return {'is_busy': is_busy, 'locks': locks}

def acquire_test_lock(locks_path, name):
    lock_state = check_test_lock(locks_path)
    if lock_state['is_busy']:
        return None, 'Lock present: %s' % lock_state['locks']

    lock_path = '%s/firebat_%s.lock' % (locks_path, name)
    try:
        #open(lock_path, 'w').close()
        open(lock_path, 'w')
    except Exception, e:
        return None, e
    return lock_path, None 

def release_test_lock(locks_path, name):
    l_path = '%s/firebat_%s.lock' % (locks_path, name)
    if not os.path.isfile(l_path):
        return None, 'No such file: %s' % l_path

    try:
        os.unlink(l_path)
    except Exception, e:
        return None, e

    return True, None
