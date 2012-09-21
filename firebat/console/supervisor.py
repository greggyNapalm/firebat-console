# -*- coding: utf-8 -*-

"""
firebat.supervisor
~~~~~~~~~~~~

Supervisor - demonized process to launch and control Phantom.
"""
import os
import sys
import time
import signal
import socket
import getpass
import logging
import datetime
import cPickle
import base64
from string import maketrans
import threading
from subprocess import Popen, PIPE
import pprint
pp = pprint.PrettyPrinter(indent=4)


import simplejson as json
from simplejson.decoder import JSONDecodeError

from firebat.console.conf import get_main_cfg
from firebat.console.helpers import get_logger
from firebat.console.aggr1 import proc_whole_phout
from firebat.clients import FirebatOverlordClient

PHANTOM_CMD = ['phantom', 'run', 'phantom.conf']


def get_sock(sock_path, to=5, qlen=1):
    '''Create TCP socket, call bind and listen.
    Args:
        sock_path: str, path to unix domain socket file.
        to: int, accept call time out.
        qlen: int, incoming TCP connections quiue length.

    Returns:
        sock: socket object.
    '''
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(to)
    sock.bind(sock_path)
    sock.listen(qlen)
    return sock


def translator(sock_path):
    '''Reply with test state in JSON format on each request.
    Args:
        sock_path: str, path to unix domain socket file.
    '''
    logger = logging.getLogger('root')
    global msg
    global run

    try:
        os.unlink(sock_path)
    except OSError:
        if os.path.exists(sock_path):
            raise

    while run:
        try:
            if not 'sock' in locals():
                sock = get_sock(sock_path)
            conn, client_addr = sock.accept()
        except socket.timeout:
            # no new connections from clients
            continue
        try:
            while True:
                data = conn.recv(1)
                if data:
                    msg_size = str(len(msg)).zfill(4)
                    conn.sendall(msg_size)
                    conn.sendall(msg)
                else:
                    break
        finally:
            # Clean up the connection
            conn.close()


class TestStatus(object):
    """Supervisor and Phantom status information container.

    Attributes:
        state: str, human readable status.
        started_at: datetime obj, time when work was started.
        duration: int, time delta in seconds from start.
        uid: str, process owner.
        owner: str, responsible person
        total_dur: int, theoretical test duration in seconds
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
    def __init__(self, test_cfg, main_cfg=None, state='Starting'):
        self.test_cfg = test_cfg
        self.logger = logging.getLogger('supervisor')
        self.pid = os.getpid()
        self.state = state
        self.started_at = datetime.datetime.utcnow()
        self.duration = 0
        self.uid = getpass.getuser()
        self.wd = os.getcwd()

        if main_cfg:
            self.main_cfg = main_cfg

        self.fires = {} 
        for idx, fire in enumerate(self.test_cfg['fire']):
            fire_up = {
                'state': 'Created',
                'end_status': None,
                'phantom_pid': None,
                'answ_mtime': None,
                'answ_mago': None,
                'retcode': None,
                'stdout': None,
                'stderr': None,
            }
            self.test_cfg['fire'][idx].update(fire_up)

    def jobs_completed(self):
        '''Check is there currentlly running phantom jobs or not.'''
        for fire in self.test_cfg['fire']:
            if fire['end_status'] == None:
                return False
        self.state = 'phantoms terminated'
        self.test_cfg['ended_at'] = datetime.datetime.utcnow()
        return True

    def run_jobs(self, sleep_time=1):
        '''Fork phantom jobs according to test_cfg
           and monitor them till the termination.
        '''
        # fork phantom for each fire in test.
        for idx, fire in enumerate(self.test_cfg['fire']):
            new_job = Popen(PHANTOM_CMD, stdout=PIPE, stderr=PIPE, cwd=fire['wd'])

            self.test_cfg['fire'][idx]['job'] = new_job 
            self.test_cfg['fire'][idx]['state'] = 'phantom launched'
            self.logger.info('%s > %s' % (fire['name'], 'Phantom launched'))
            self.test_cfg['fire'][idx]['phantom_pid'] = new_job.pid
            self.logger.info('%s > %s %s' % (fire['name'], 'Phantom PID:',
                                             new_job.pid))
            self.state = 'Phantoms forked'


        # sleep and pool each child process.
        end_status = 0  # by default All is ok.

        if self.main_cfg:
            self.oc = FirebatOverlordClient(self.main_cfg['FIERBAT_API_URL'],
                                            self.main_cfg['FIERBAT_API_TO'])

        if self.oc: # push updates to overlord if needed.
            retcode, resp = self.oc.push_test_updates(self.test_cfg,
                                                      status='running')
            self.logger.info('Push test status update to Overlord side.')
 
        while not self.jobs_completed():
            self.duration_update()
            self.log_mtime_update()

            for idx, fire in enumerate(self.test_cfg['fire']):
                if fire['end_status'] != None:  # fire allready terminated
                    continue
                job = self.test_cfg['fire'][idx]['job']
                retcode = job.poll()
                if retcode is not None:  # Process finished.
                    self.test_cfg['fire'][idx]['retcode'] = retcode
                    self.test_cfg['fire'][idx]['stdout'] = job.stdout.read()
                    self.test_cfg['fire'][idx]['stderr'] = job.stderr.read()
                    self.test_cfg['fire'][idx]['ended_at'] = datetime.datetime.utcnow()
                    self.test_cfg['fire'][idx]['state'] = 'phantom terminated'
                    self.logger.info(
                        '%s > phantom terminated with retcode: %s' %\
                        (fire['name'], retcode))
                    self.test_cfg['fire'][idx]['end_status'] = end_status
                    if self.oc: # push updates to overlord if needed.
                        f = self.test_cfg['fire'][idx]
                        #self.logger.info('Try to patch fire on Overlord side.') 
                        self.logger.info('%s > %s' % (f['name'],
                            'Try to patch fire on Overlord side.')) 
                        # Push fire termination details to remote side.
                        self.oc.push_fire_updates(f)

                        # Calculate metrics from phout and push them after.
                        result, msg = proc_whole_phout(f, oc=self.oc)
                        if result:
                            self.logger.info('%s > %s' % (f['name'],
                                'Fire updated on remote side successfully.')) 
                        else:
                            self.logger.info('%s > %s' % (f['name'],
                                'Remote call failed: %s' % msg)) 


                else:  # No process is done, wait a bit and check again.
                    self.state = 'Phantoms waiting'
                    time.sleep(sleep_time)
                    self.msg_update()
                    try:
                        astop_mtime =\
                            self.test_cfg['fire'][idx]['autostop']['astop_mtime']
                    except KeyError:
                        astop_mtime = None
                    if astop_mtime and \
                        self.test_cfg['fire'][idx]['answ_mago'] > astop_mtime:
                        self.logger.error('phantom answ file hasn\'t been' +
                                          ' updated to long')
                        self.logger.error('Try to stop the fire')
                        job.kill()
                        end_status = -1

        if self.oc: # push updates to overlord if needed.
            #self.test_cfg['ended_at'] = datetime.datetime.utcnow()
            retcode, resp = self.oc.push_test_updates(self.test_cfg,
                                                      status='finished')
            self.logger.info('Push test status update to Overlord side.')


    def msg_update(self):
        '''Update JSON obj translated to other process'''
        global msg
        msg = json.dumps(self.repr_as_dict())

    def log_result(self):
        '''Log info about how phantom was terminated.'''
        for idx, fire in enumerate(self.test_cfg['fire']):
            if fire['end_status'] == None:
                continue
            result = 'undefined'
            if fire['end_status'] == 0:
                result = 'phantom terminated normally'
                if fire['retcode'] == -9:
                    result = 'phantom killed by user with SIGNUM 9'
            elif fire['end_status'] == -1:
                result = 'phantom terminated by supervisor, reason: answ mtime'

            self.logger.info('%s > %s' % (fire['name'], result))


    def duration_update(self):
        delta = datetime.datetime.utcnow() - self.started_at
        self.duration = delta.seconds

    def log_mtime_update(self, log_name='answ.txt'):
        '''Check when Phantom write one of his log files last time,
        helps to check, is Phantom alive or not.'''
        for idx, fire in enumerate(self.test_cfg['fire']):
            log_path = '%s/%s' % (fire['wd'], log_name)
            try:
                mtime = os.path.getmtime(log_path)
                self.test_cfg['fire'][idx]['answ_mtime'] = time.ctime(mtime)
                delta = datetime.datetime.now() -\
                    datetime.datetime.fromtimestamp(int(mtime))
                self.test_cfg['fire'][idx]['answ_mago'] = delta.seconds
            except OSError:
                self.logger.warning('Can\'t read mtime of file: %s' % log_path)

    def repr_as_dict(self):
        '''Represent current test status as a dict.'''
        self.duration_update()
        self.log_mtime_update()
        result = {
            'test_name': self.test_cfg['title']['test_name'],
            'pid': self.pid,
            'id': self.test_cfg.get('id', None),
            'task': self.test_cfg['title']['task'],
            'duration': self.duration,
            'started_at': self.started_at.isoformat(),
            'state': self.state,
            'owner': self.test_cfg.get('owner', 'uid'),
            'uid': self.uid,
            'fires': [],
        }
        fire_allowed = [
            'answ_mago',
            'name',
            'phantom_pid',
            'total_dur',
        ]
        for idx, fire in enumerate(self.test_cfg['fire']):
            f = dict((key,value) for key, value in fire.iteritems() if key in\
                    fire_allowed)
            result['fires'].append(f)

        return result
    #def put(self):
    #    '''React on USR1 signal, put collected data on file system.'''
    #    file_path = '/tmp/%s.fire' % self.pid
    #    file(file_path, 'w').write(str(self.jsonify()))
    #    return file_path



def drop_pid(name, pid, pid_dir='/var/run', stamp=False):
    if stamp:
        if not os.path.exists(pid_dir):
            os.makedirs(pid_dir)
        time_str = "%.6f" % time.time()
        time_str = time_str.translate(maketrans('.', '_'))
        pid_file = pid_dir + '/' + name + '_%s.pid' % time_str
    else:
        pid_file = './' + name + '.pid'

    with open(pid_file, 'w') as pid_fh:
        pid_fh.write(pid)
    return pid_file


def update_fire(status, json_path='.fire.json'):
    '''Update fire dict according to status object.
    Args:
        status: obj, current status object.
        json_path: str, file path fire dict shud be readed from.

    Returns:
        put new JSON file to fire working directory.
    '''
    logger = logging.getLogger('root')
    new_path = '.fire_up.json'
    try:
        with open(json_path, "r") as fire_fh:
            fire = json.loads(fire_fh.read())
    except IOError, e:
        logger.error('Could not read "%s": %s\n' % (json_path, e))
    except JSONDecodeError, e:
        logger.error('Could not parse fire config file: %s\n%s' % (json_path,
                                                                   e))
    fire['owner'] = status.owner
    fire['uid'] = status.uid
    fire['total_dur'] = status.total_dur
    fire['started_at'] = status.started_at.strftime('%s')
    fire['src_host'] = socket.getfqdn()
    new_cfg = json.dumps(fire, indent=4 * ' ')
    try:
        with open(new_path, "w+") as fire_fh:
            fire_fh.write(new_cfg)
    except IOError, e:
        logger.error('Could not write "%s": %s\n' % (new_path, e))


#def run(test_cfg):
#    '''Shud be called with python-daemon context manager.
#    Args:
#        log_path: str, path to new log file.
#        log_lvl: int
#    '''
#    # put PID file two times, one for debug
#    pid_p = drop_pid('fire',
#                     str(os.getpid()),
#                     pid_dir='/tmp/fire/',
#                     stamp=True)
#    drop_pid('fire', str(os.getpid()), pid_dir='./')
#    logger = get_logger(log_path='./fire.log', stream=False, is_debug=True)
#
#    #opts = None
#    #if (len(sys.argv) > 1):
#    #    opts = cPickle.loads(base64.b64decode(sys.argv[1]))
#
#    status = FireStatus(opts)
#    logger.info('PID file: %s' % pid_p)
#    logger.info('PID: %s' % os.getpid())
#
#    logger.info('Starting')
#
#    # use unix domain socket in thread for IPC
#    sock_dir = '/tmp/fire/sock'
#    if not os.path.exists(sock_dir):
#        os.makedirs(sock_dir)
#    sock_path = '%s/%s.sock' % (sock_dir, status.pid)
#    global run
#
#    run = True
#    t1 = threading.Thread(target=translator, args=(sock_path,))
#    t1.start()
#
#    end_status = run_phantom(status)
#    run = False
#
#    # before exit part
#    fire_id = opts.get('id', None)
#    if fire_id:
#        main_cfg = get_main_cfg()
#        oc = FirebatOverlordClient(main_cfg['FIERBAT_API_URL'],
#                                   main_cfg['FIERBAT_API_TO'])
#
#        retcode, err = oc.push_fire_updates(fire_id, status='finished',
#                            ended_at=datetime.datetime.utcnow().isoformat())
#        if retcode:
#            logger.info('Fire-overlord API call > fire updated successfully.')
#        else:
#            logger.error('Fire-overlord API call failed: %s' % err)
#
#    logger.debug(str(status.jsonify()))
#    os.unlink(pid_p)
#
#    if end_status == 0:
#        logger.info('Phantom job completed normally.')
#    elif end_status == 1:
#        logger.info('Phantom was killed by supervisor, reason:answ file mtime')
#    elif status.retcode == -9:
#        logger.info('Phantom was killed by user')
#
#    logger.info('Exiting')

def run1(test_cfg, main_cfg):
    logger = get_logger(log_path='%s/fire.log' % test_cfg['wd'],
                        name='supervisor')
    logger.info('Supervisor started')

    pid_path = drop_pid('fire', str(os.getpid()), pid_dir=main_cfg['PID_DIR'], stamp=True)
    logger.info('PID file: %s' % pid_path)
    logger.info('PID: %s' % os.getpid())

    test_status = TestStatus(test_cfg, main_cfg=main_cfg)

    # use unix domain socket in thread for IPC
    sock_dir = main_cfg.get('SOCKET_DIR', '/tmp/fire/sock')
    if not os.path.exists(sock_dir):
        os.makedirs(sock_dir)
    sock_path = '%s/%s.sock' % (sock_dir, test_status.pid)
    logger.info('Sock file: %s' % sock_path)
    global run
    global msg
    msg = json.dumps({'check': True})

    run = True
    t1 = threading.Thread(target=translator, args=(sock_path,))
    t1.start()

    test_status.run_jobs()
    test_status.log_result()
    run = False

    # on exit
    os.unlink(sock_path)
    os.unlink(pid_path)
    logger.info('Supervisor exiting')

if __name__ == '__main__':
    print '#' * 80
    print 'DUBUG MODE, FOR DEVELOPMENT ONLY'
    print '#' * 80, '\n' * 4
    with open('.test_cfg.json', 'r') as test_debug_fh,\
        open('.main_cfg.json', 'r') as main_debug_fh:
        test_cfg = json.loads(test_debug_fh.read())
        main_cfg = json.loads(main_debug_fh.read())

    run1(test_cfg, main_cfg)
