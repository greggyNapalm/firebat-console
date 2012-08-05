# -*- coding: utf-8 -*-

"""
firebat.helpers
~~~~~~~~~~~~~~~

A set of functions and tools to help in routine
"""

import sys
import logging
import commands
import pprint
pp = pprint.PrettyPrinter(indent=4)

import validictory


def exit_err(msg):
    '''On critical error, write out msg and exit.
    Args:
        msg: str or list.
    '''
    logger = logging.getLogger('firebat.console')
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


def get_logger(is_debug=False):
    '''Return logger obj with console hendler.
    '''
    logger = logging.getLogger('firebat.console')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    if is_debug:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s  %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)
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
