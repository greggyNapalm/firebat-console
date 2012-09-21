#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
firebat.clients
~~~~~~~~~~~~~~~

Remote API clients.
"""
import os
import socket
import logging

import requests
import simplejson as json

from firebat import __version__


class FirebatOverlordClient(object):
    '''Firebat-overlord REST API client'''
    def __init__(self, api_url, client_to):
        self.base_url = api_url
        self.to = client_to
        self.agent = 'firebat v%s' % __version__
        self.statuses = {
            'created': 1,
            'started': 2,
            'running': 3,
            'aborted': 4,
            'finished': 5,
        }

    def ping(self):
        '''Check remote API availability.'''
        try:
            r = requests.get('%s/ping' % self.base_url,
                             timeout=self.to)
        except socket.error, e:
            return False, e
        except requests.exceptions.Timeout, e:
            return False, e

        if r.status_code == 204:
            return True, 'Reachable'
        else:
            return False, 'resp status code: %s' % r.status_code

    def registrate_new_test(self, test_cfg):
        '''Register test on API side, get test id and fires ids in responce'''
        body = {
            'status': self.statuses['started'],
            'cfg': test_cfg,
        }
        try:
            r = requests.post('%s/test' % self.base_url,
                              data=json.dumps(body), timeout=self.to,
                              headers={'content-type': 'application/json'})
        except socket.error, e:
            return False, e
        except requests.exceptions.Timeout, e:
            return False, e

        if r.status_code == 201:
            return True, r.json
        else:
            return False, 'resp status code: %s' % r.status_code

    def push_test_updates(self, test, status=None):
        '''PATCH test entrie on API side.'''
        body = {
            'id': test['id'],
        }

        if status:
            status_id = self.statuses.get(status, None)
            if status_id:
                body['status_id'] = status_id

        if 'ended_at' in test:
            body['ended_at'] = test['ended_at'].isoformat()

        try:
            r = requests.patch('%s/test' % self.base_url,
                             data=json.dumps(body), timeout=self.to,
                             headers={'content-type': 'application/json'})
        except socket.error, e:
            return False, e
        except requests.exceptions.Timeout, e:
            return False, e

        if r.status_code == 204:
            return True, None
        else:
            return False, 'resp status code: %s' % r.status_code

    def push_fire_updates(self, fire):
        '''PATCH fire entrie on API side.'''
        body = {
            'id': fire['id'],
        }

        if 'ended_at' in fire:
            body['ended_at'] = fire['ended_at'].isoformat()

        if 'end_status' in fire:
            if fire['end_status'] < 0:
                body['status_id'] = self.statuses['aborted']
            else:
                body['status_id'] = self.statuses['finished']

        if 'result' in fire:
            body['result'] = fire['result']

        try:
            r = requests.patch('%s/fire' % self.base_url,
                             data=json.dumps(body), timeout=self.to,
                             headers={'content-type': 'application/json'})
        except socket.error, e:
            return False, e
        except requests.exceptions.Timeout, e:
            return False, e

        if r.status_code == 204:
            return True, None
        else:
            return False, 'resp status code: %s' % r.status_code


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
        ammo_resource = '%s/%s' % (api_url, ammo_url)
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

