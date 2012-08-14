#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
firebat.clients
~~~~~~~~~~~~~~~

Remote API clients.
"""
import socket

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

    def registrate_new_test(self, test_cfg):
        '''Register test on API side, get test id and fires ids in responce'''
        body = {
            'status': self.statuses['started'],
            'cfg': test_cfg,
        }
        try:
            r = requests.post('%s/test/firebat' % self.base_url,
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

    def push_fire_updates(self, fire_id, fire_cfg=None, status=None,
                          ended_at=None):
        '''PATCH fire_cfg entrie on API side.'''
        if fire_cfg:
            body = {
                'cfg': fire_cfg,
            }
        else:
            body = {}

        if status:
            body.update({'status': self.statuses[status]})

        if ended_at:
            body.update({'ended_at': ended_at})

        try:
            r = requests.put('%s/fire/%s' % (self.base_url, fire_id),
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
