# -*- coding: utf-8 -*-

"""
firebat.launcher
~~~~~~~~~~~~~~~

Start new POSIX process for Phantom supervisor and monitor it.
"""

import os
import time
import signal
import getpass
import logging
import simplejson as json
import datetime
from subprocess import Popen, PIPE

# const
PID_FILE='./fire.pid'
PHANTOM_PID_FILE = './phantom.pid'
PHANTOM_CMD = ['phantom', 'run', 'phantom.conf']


class FireStatus(object):
    """Supervisor and Phantom status information singleton.

    Attributes:
        state: str, human readable status.
        started_at: datetime obj, time when work was started.
        duration: int, time delta in seconds from start.
        uid: str, process owner.
        wd: str, working directory if process.
        pid: int, supervisor PID.
        phantom_pid: int, Phantom process PID.
        answ_mtime: str, time when answ.txt was last time writen by Phantom.
        answ_mago: int, number of seconds since answ_mtime moment.
        retcode: int, Phantom process exit code.
        stdout: str, Phantom process STDOUT.
        stderr: str, Phantom process STDERR.
        eggs: An integer count of the eggs we have laid.
    """
    def __init__(self, state='Starting', logger=None):
        if logger:
            self.logger = logger
        else:
            self.logger = get_logger()
        self.state = state
        self.started_at = datetime.datetime.now()
        self.duration = 0
        self.uid = getpass.getuser()
        self.wd = os.getcwd()
        self.pid = os.getpgid(0)
        self.phantom_pid = None
        self.answ_mtime = None
        self.answ_mago = None
        self.retcode = None
        self.stdout = None
        self.stderr = None

    def duration_update(self):
        delta = datetime.datetime.now() - self.started_at
        self.duration = delta.seconds

    def log_mtime_update(self):
        '''Check when Phantom write one of his log files last time,
        helps to check, is Phantom alive or not.'''
        log_path = './answ.txt'
        try:
            mtime = os.path.getmtime(log_path)
            self.answ_mtime = time.ctime(mtime)
            delta = datetime.datetime.now() -\
                datetime.datetime.fromtimestamp(int(mtime))
            self.answ_mago = delta.seconds

        except OSError:
            self.logger.error('Can\'t read mtime of file: %s' % log_path)

    def jsonify(self):
        '''Represent collected data in human readable format'''
        result = {
            'state': self.state,
            'wd': self.wd,
            'pid': self.pid,
            'uid': self.uid,
            'phantom_pid': self.phantom_pid,
            'duration': self.duration,
            'answ_mtime': self.answ_mtime,
            'answ_mago': self.answ_mago,
            'retcode': self.retcode,
            'stdout': self.stdout,
            'stderr': self.stderr,
        }
        return json.dumps(result, sort_keys=True, indent=4 * ' ')

    def put(self):
        '''React on USR1 signal, put collected data on file system.'''
        file_path = '/tmp/%s.fire' % self.pid
        file(file_path, 'w').write(str(self.jsonify()))
        return file_path
                
def drop_pid(name, pid):
    file('./' + name + '.pid', 'w').write(pid)

def get_logger(log_path='./fire_launcher.log', log_lvl=logging.DEBUG):
    '''Create logger object.
    Args:
        log_path: str, path to new log file.
        log_lvl: int, 

    Returns:
        logger obj
    '''

    logger = logging.getLogger('firebat.launcher')
    logger.setLevel(logging.DEBUG)
    fh = logging.FileHandler(log_path)
    fh.setLevel(log_lvl)
    formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    return logger


def run_phantom(status, sleep_time=1, logger=None):
    '''Create new POSIX process and wait until exit.
    Args:
        status: obj, FireStatus instance to collect monitorring data.
        sleep_time: int, time interval between iterations.
        logger: obj, logger instance.
    '''

    if not logger:
        logger = get_logger()
    logger.debug('Phantom launch')
    job = Popen(PHANTOM_CMD, stdout=PIPE, stderr=PIPE)
    status.state = 'phantom launched'
    status.phantom_pid = job.pid
    status.state = 'phantom working'
    drop_pid('phantom', str(job.pid))
    while 1:
        status.duration_update()
        status.log_mtime_update()
        retcode = job.poll()
        if retcode is not None: # Process finished.
            status.retcode = retcode
            status.stdout = job.stdout.read()
            status.stderr = job.stderr.read()
            status.state = 'phantom exited'
            logger.debug('phantom exited with retcode: %s' % retcode)
            #sys.stdout.write(str(status.jsonify()) + '\n')
            break
        else: # No process is done, wait a bit and check again.
            time.sleep(sleep_time)

def run_supervisor():
    '''Shud be called in new daemon process to run and check phantom tool
    Args:
        log_path: str, path to new log file.
        log_lvl: int, 
    '''
    drop_pid('fire_launcher', str(os.getpid()))
    logger = get_logger()
    drop_pid('fire_launcher1', str(os.getpid()))
    status = FireStatus(logger=logger)

    logger.info('Starting')
    def sig_usr1_handler(signum, frame):
        file_path = status.put()
        logger.debug('USR1 signal catched. See info in: %s' % file_path)
        return

    signal.signal(signal.SIGUSR1, sig_usr1_handler )
    run_phantom(status, logger=logger)
    #time.sleep(7)
    #status.log_mtime_update()
   
    logger.debug(str(status.jsonify())) 
    logger.info('Exiting')

if __name__ == '__main__':
    run_supervisor()
