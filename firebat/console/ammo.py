# -*- coding: utf-8 -*-

"""
firebat.ammo
~~~~~~~~~~~~

Load tests input data generators.
"""
import io
import httplib
import urllib


class HttpCompiler(object):
    def __init__(self, cntx_up=None, logger=None):
        self.defaults = {
            'method': 'GET',
            'Host': 'target.on-fire.io',
            'kwargs': {},
        }
        self.cntx = self.defaults
        if cntx_up:
            self.cntx.update(cntx_up)

        conn = httplib.HTTPConnection(self.cntx['Host'])
        bio = io.BytesIO()
        bio.sendall = bio.write
        conn.sock = bio
        conn.request(self.cntx['method'], '%s', **self.cntx['kwargs'])
        self.tmpl = bio.getvalue().decode('utf-8')

    def build_req(self, qs):
        return self.tmpl % qs
