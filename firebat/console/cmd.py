# -*- coding: utf-8 -*-

"""
firebat.cmd
~~~~~~~~~~~~~~~

Command line interface for Firebat.
"""

import os
import signal
import logging
import pprint
pp = pprint.PrettyPrinter(indent=4)

import simplejson as json
from simplejson.decoder import JSONDecodeError


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


def get_running_fires(pids_path='/tmp/fire/', logger=None):
    '''Read PID files from folder and fillter out currently running.
    Args:
        pids_path: str, wahere PID files stored.
        logger: logger object

    Returns:
        generator object, yield pids.
    '''
    logger = logging.getLogger('firebat.console')
    if not logger.handlers:
        logger = get_logger()

    if not os.path.exists(pids_path):
        logger('No active fires found.' +
               'PIDs folder doesn\'t exist: %s' % pids_path)
        return

    for pid_file in os.listdir(pids_path):
        with open(pids_path + pid_file, 'r') as pid_fh:
            pid = int(pid_fh.read())
        if os.path.exists('/proc/%s' % pid):
            yield pid


def get_fire_info(pid, dumps_pth='/tmp', logger=None):
    '''Read fire status by dump from file system.
    Args:
        pid: int, fire PID.
        dumps_pth: str, where to find dump files.
        logger: logger object.

    Returns:
        state: dict, fire state.
    '''
    logger = logging.getLogger('firebat.console')
    if not logger.handlers:
        logger = get_logger()
    state = None
    try:
        path = '%s/%s.fire' % (dumps_pth, pid)
        with open(path, 'r') as state_fh:
            state_json = state_fh.read()
        state = json.loads(state_json)
    except IOError as e:
        logger.error('Can\'t read state dump from: %s' % path)
    except JSONDecodeError, e:
        logger.error('Can\'t parse fire status data geted from: %s\n%s' %\
                     (path, e))
    return state


def get_running_jobs(pids_path='/tmp/fire/', logger=None):
    '''Collect and print out running fires details.
    Args:
        pids_path: where to search PID files.
        logger: logger object.

    Returns:
        Just print to STDOUT.
    '''
    logger = logging.getLogger('firebat.console')
    if not logger.handlers:
        logger = get_logger()

    cnt = 0
    for pid in get_running_fires(logger=logger):
        cnt += 1
        # to get job state on file system, We need to send SIGUSR1 to process
        os.kill(pid, signal.SIGUSR1)
        fire = get_fire_info(pid, logger=logger)
        if fire:
            for key, val in fire.iteritems():
                print '%15s: %s' % (key, val)
            ready = (fire['duration'] / float(fire['total_dur'])) * 100
            print '%15s: %0.2f%%' % ('ready', ready)
            print '-' * 80
    if cnt == 0:
        logger.info('No active fires found.')


def kill_all(pids_path='/tmp/fire/', logger=None):
    '''Kill all currently running fires..
    Args:
        pids_path: where to search PID files.
        logger: logger object.

    Returns:
        Just logs result to STDOUT.
    '''
    logger = logging.getLogger('firebat.console')
    if not logger.handlers:
        logger = get_logger()

    cnt = 0
    for pid in get_running_fires(logger=logger):
        cnt += 1
        fire = get_fire_info(pid, logger=logger)
        logger.info('send SIGKILL to: %s' % fire['phantom_pid'])
        os.kill(fire['phantom_pid'], signal.SIGKILL)
    if cnt == 0:
        logger.info('Nothing to kill.')
