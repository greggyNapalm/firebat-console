# -*- coding: utf-8 -*-

"""
firebat.cmd
~~~~~~~~~~~~~~~

Command line interface for Firebat.
"""

import os
import signal
import logging
import commands
import time
import datetime
import pprint
pp = pprint.PrettyPrinter(indent=4)

import simplejson as json
from simplejson.decoder import JSONDecodeError
import zmq


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
        logger.info('No active fires found.' +
            'PIDs folder doesn\'t exist: %s' % pids_path)
        return

    for pid_file in os.listdir(pids_path):
        if pid_file.endswith('.pid'):
            try:
                with open(pids_path + pid_file, 'r') as pid_fh:
                    pid = int(pid_fh.read())
            except IOError:
                continue  # file was deleted or any other IO problem
            if os.path.exists('/proc/%s' % pid):
                yield pid


def get_fire_info(pid, logger=None, sock_dir='/tmp/fire/sock'):
    '''Read fire status by dump from file system.
    Args:
        pid: int, fire PID.
        sock_dir: str, where to search for fire sockets for IPC.
        logger: logger object.

    Returns:
        state: dict, fire state.
    '''
    logger = logging.getLogger('firebat.console')
    if not logger.handlers:
        logger = get_logger()
    state = None

    context = zmq.Context()
    work_receiver = context.socket(zmq.PULL)
    addr = 'ipc://%s/%s.sock' % (sock_dir, pid)
    work_receiver.connect(addr)

    poller = zmq.Poller()
    poller.register(work_receiver, zmq.POLLIN)
    socks = dict(poller.poll(1500))  # in milliseconds
    if socks:
        if socks.get(work_receiver) == zmq.POLLIN:
            try:
                msg = work_receiver.recv(zmq.NOBLOCK)
                state = json.loads(msg)
            except JSONDecodeError, e:
                logger.error('Can\'t parse fire status data geted' +
                        ' from: %s\n%s' % (pid, e))
    else:
        logger.error('Time out waiting state msg from fire PID: %s' % pid)
    return state


def list_running_jobs(pids_path='/tmp/fire/', logger=None):
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
        fire = get_fire_info(pid)
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
    SLP_TIME = 0.1
    WAIT_TO = 2
    logger = logging.getLogger('firebat.console')
    if not logger.handlers:
        logger = get_logger()

    cnt = 0
    for pid in get_running_fires(logger=logger):
        cnt += 1
        fire = get_fire_info(pid, logger=logger)
        logger.info('send SIGKILL to: %s' % fire['phantom_pid'])
        os.kill(fire['phantom_pid'], signal.SIGKILL)
        ready = False
        t_start = datetime.datetime.now()
        while not ready:
            t_delta = datetime.datetime.now() - t_start
            if t_delta.seconds > WAIT_TO:
                msg = 'Phantom still working, kill em manually.'
                break
            elif (os.path.exists('/proc/%s' % fire['pid']) or\
                   os.path.exists('/proc/%s' % fire['pid'])):
                time.sleep(SLP_TIME)
            else:
                msg = 'Killed successfully.'
                break
        logger.info('`-> %s' % msg)

    if cnt == 0:
        logger.info('Nothing to kill.')
