# -*- coding: utf-8 -*-

"""
firebat.helpers
~~~~~~~~~~~~~~~

A set of functions and tools to help in routine
"""

import os
import sys
import socket
import logging
import commands
import shutil
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
    '''Return logger obj with console hendler.
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


def validate(sample, tgt='test'):
    ''' Check test dict structure: required keys and their types.
    Args:
        sample: dict, data to validate.
        tgt: str, part of fb input data(whole test or fire only).

    Returns:
        Raise exception on invalid sample.
    '''
    assert tgt in ['test', 'fire']
    fire_schema = {
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

    test_schema = {
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
                    'type': fire_schema,
                },
            },
        },
    }

    if tgt == 'test':
        validictory.validate(sample, test_schema)
    elif tgt == 'fire':
        validictory.validate(sample, fire_schema)

    return True

def fetch_from_armorer(ammo_url,
                       api_url=None,
                       local_path='./armorer/ammo.gz'):
    ''' Check test dict structure: required keys and their types.
    Args:
        ammo_url: str, direct file URL or armorer API path.
        api_url: str, base armorer REST API url.
        local_path: str, path to store downloaded data.

    Returns:
        local_path: str.
    '''
    assert isinstance(ammo_url, basestring)

    logger = logging.getLogger('root')

    agent = 'firebat %s' % socket.gethostname()

    if ammo_url.startswith('http://'):
        archive_url = ammo_url
    elif ammo_url.endswith('/last'):
        ammo_resource =  '%s/%s' % (api_url, ammo_url)
        ra = requests.get(ammo_resource, headers={'User-Agent': agent})
        ra.raise_for_status()
        archive_url = ra.json['url']

    logger.info('Fetching ammo from: %s' % archive_url)
    r = requests.get(archive_url, headers={'User-Agent': agent})
    r.raise_for_status()

    size = int(r.headers['Content-Length'].strip())
    logger.info('Ammo size is: %s bytes(%s MB)' % (size, size / (1024 * 1024)))

    dirs_in_local_path = '/'.join(local_path.split('/')[:-1])
    if not os.path.exists(dirs_in_local_path):
        os.makedirs(dirs_in_local_path)

    with open(local_path, 'wb') as local_fh:
        for line in r.content:
            local_fh.write(line)

    return local_path
