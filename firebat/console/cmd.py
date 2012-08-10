# -*- coding: utf-8 -*-

"""
firebat.cmd
~~~~~~~~~~~~~~~

Command line interface for Firebat.
"""

import os
import signal
import logging
import time
import datetime
import socket
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


def get_running_fires(pids_path='/tmp/fire/'):
    '''Read PID files from folder and fillter out currently running.
    Args:
        pids_path: str, wahere PID files stored.
        logger: logger object

    Returns:
        generator object, yield pids.
    '''
    logger = logging.getLogger('root')
    #logger = logging.getLogger('firebat.console')
    #if not logger.handlers:
    #    logger = get_logger()

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


def get_fire_info(pid, sock_dir='/tmp/fire/sock'):
    '''Read fire status from unix socket.
    Args:
        pid: int, fire PID.
        sock_dir: str, where to search for fire sockets for IPC.
        logger: logger object.

    Returns:
        state: dict, fire state.
    '''
    logger = logging.getLogger('root')
    #logger = logging.getLogger('firebat.console')
    #if not logger.handlers:
    #    logger = get_logger()
    state = None

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock_path = '%s/%s.sock' % (sock_dir, pid)

    try:
        sock.connect(sock_path)
    except socket.error:
        logger.error('Can\'t connect to fire socket: %s' % sock_path)
        return state

    try:
        sock.sendall('.')
        msg_size = int(sock.recv(4))
        msg_s = sock.recv(msg_size)
    finally:
        sock.close()

    try:
        state = json.loads(msg_s)
    except JSONDecodeError, e:
        logger.error('Can\'t parse fire status data geted' +
                     ' from: %s\n%s' % (pid, e))
    return state


def list_running_jobs(pids_path='/tmp/fire/', logger=None):
    '''Collect and print out running fires details.
    Args:
        pids_path: where to search PID files.
        logger: logger object.

    Returns:
        Just print to STDOUT.
    '''
    logger = logging.getLogger('root')
    #logger = logging.getLogger('firebat.console')
    if not logger.handlers:
        logger = get_logger()

    cnt = 0
    for pid in get_running_fires():
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


def kill_all(pids_path='/tmp/fire/'):
    '''Kill all currently running fires..
    Args:
        pids_path: where to search PID files.
        logger: logger object.

    Returns:
        Just logs result to STDOUT.
    '''
    SLP_TIME = 0.1
    WAIT_TO = 2
    #logger = logging.getLogger('firebat.console')
    logger = logging.getLogger('root')
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
