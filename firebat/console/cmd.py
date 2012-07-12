# -*- coding: utf-8 -*-

"""
firebat.cmd
~~~~~~~~~~~~~~~

Command line interface for Firebat.
"""

import os
import signal
import simplejson as json


def get_running_jobs(pids_path='/tmp/fire/'):
    ''' Read jobs PID files, send signals to them, get current state and
    display it to user.
    Args:
        pids_path: str, where to find the PID files.
    '''

    no_data_msg = 'No active fires found.'

    if not os.path.exists(pids_path):
        print no_data_msg
        return

    state = {}
    for pid_file in os.listdir(pids_path):
        state[pid_file] = {}
        with open(pids_path + pid_file, "r") as pid_fh:
            state[pid_file]['pid'] = int(pid_fh.read())

        state[pid_file]['proc_exist'] = False
        # check that job process exist.
        if os.path.exists('/proc/%s' % state[pid_file]['pid']):
            state[pid_file]['proc_exist'] = True
            # to get job state on file system, We need to send SIG
            os.kill(state[pid_file]['pid'], signal.SIGUSR1)
    if len(state) == 0:
        print no_data_msg
        return

    for key, pid_file in state.iteritems():
        try:
            path = '/tmp/%s.fire' % pid_file['pid']
            with open(path) as state_fh:
                state_json = state_fh.read()
                pid_file['state'] = json.loads(state_json)
        except IOError as e:
            print 'Can\'t read state dump from: %s' % path
        except json.decoder.JSONDecodeError, e:
            print 'Can\'t parse status data geted from: %s' % path

    for key, pid in state.iteritems():
        print '\n', key, '\n', len(key) * '-'
        try:
            lines = [
                ('state', pid['state']['state']),
                ('duration', pid['state']['duration']),
                ('total duration', pid['state']['total_dur']),
                ('owner', pid['state']['owner']),
                ('uid', pid['state']['uid']),
                ('fire PID', pid['pid']),
                ('phantom PID', pid['state']['phantom_pid']),
                ('log mtime', pid['state']['answ_mtime']),
                ('log last mod', pid['state']['answ_mago']),
                ('wd', pid['state']['wd'])
            ]
            for chunk in lines:
                print '%15s: %s' % chunk

        except KeyError, e:
            print 'Can\'t found the key: %s' % e
