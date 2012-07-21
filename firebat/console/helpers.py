# -*- coding: utf-8 -*-

"""
firebat.helpers
~~~~~~~~~~~~~~~

A set of functions and tools to help in routineю
"""

import sys
import logging
import commands
import pprint
pp = pprint.PrettyPrinter(indent=4)


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


def get_wb_by_pid(pid):
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


def validate_dict(d, req, msg=None):
    ''' Check that all keys from required list present in tested dict.
    '''
    present_keys = d.keys()
    diff = [val for val in req if val not in present_keys]
    if len(diff) != 0:
        if not msg:
            msg = 'You missed required options in conf:'
        raise ValueError(msg + '  %s' % diff)
