# -*- coding: utf-8 -*-

"""
firebat.helpers
~~~~~~~~~~~~~~~

A set of functions and tools to help in routine
"""

import os
import sys
import signal
import errno
import fcntl
import time
import socket
import logging
import commands
import getpass
from pwd import getpwuid
from contextlib import contextmanager
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
        if m:
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


def get_logger(log_path=None, stream=True, is_debug=False, name='root'):
    '''Return logger obj.
    '''
    logger = logging.getLogger(name)
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

def check_luna_lock(locks_path):
    is_busy = False
    locks = []
    for f in os.listdir(locks_path):
        if f.startswith('lunapark_') and f.endswith('.lock'):
            f_path = '%s/%s' % (locks_path, f)
            #d
            print f_path
            is_busy = True
            locks.append({
                'file_name': f,
                'created_at': os.path.getmtime(f_path),
                'owner': owner_by_path(f_path),
            })
    return {'is_busy': is_busy, 'locks': locks}


@contextmanager
def timeout(seconds):
    '''Helps to stop blocking sys calls by signals.'''
    def timeout_handler(signum, frame):
        pass

    original_handler = signal.signal(signal.SIGALRM, timeout_handler)

    try:
        signal.alarm(seconds)
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, original_handler)


def get_lock(fileno, lck_to=2, exclusive=False, luna_lcks_path='/var/lock'):
    '''Try to acquire loack with flock sys call.'''
    # workaround fro lunapark locking mechanism
    luna_lck = check_luna_lock(luna_lcks_path)
    if luna_lck['is_busy']:
        return False, luna_lck['locks']

    with timeout(lck_to):
        try:
            if exclusive:
                fcntl.flock(fileno, fcntl.LOCK_EX)
            else:
                fcntl.flock(fileno, fcntl.LOCK_SH)
        except IOError, e:
            if e.errno != errno.EINTR:
                raise e
            return False, None
    return True, None
