# -*- coding: utf-8 -*-

"""
firebat.agr
~~~~~~~~~~~

Aggregate test results.
"""

import os
import sys
import time
import signal
import getpass
import logging
import simplejson as json
import datetime
from subprocess import Popen, PIPE
try:
    from http_parser.parser import HttpParser
except ImportError:
    from http_parser.pyparser import HttpParser

import pprint
pp = pprint.PrettyPrinter(indent=4)


class Statistic(object):
    def __init__(self):
        self.codes = []
        self.status_code = {
            'total': 0.0,
        }

    def add_responce(self, resp, txt):
        self.status_code['total'] += 1
        try:
            self.status_code[str(resp.get_status_code())] += 1
        except KeyError:
            self.status_code[str(resp.get_status_code())] = 1
            self.codes.append(str(resp.get_status_code()))
        #if resp.get_status_code() == 0:
        #    print txt, '\n', '1' * 20

    def represent(self):
        result = {
            'status_codes': self.status_code,
        }
        pp.pprint(result)
        #for c in self.codes:
        #    print '%4s %10s %13s' % \
        #        (c,
        #         str(self.result[c] / self.result['total'] * 100) + '%',
        #         self.result[c])


def answ_parser(answ_fh):
    while 1:
        l = answ_fh.readline()
        if not l:
            break
        try:
            req_size, resp_size, rtt_ms, resp_mks, errno = l.rstrip().split()
        except ValueError:
            print 'Malformed meta line in answ file.'
        req_plain = answ_fh.read(int(req_size))
        answ_fh.read(1)  # delimiter line
        resp_plain = answ_fh.read(int(resp_size))
        #answ_fh.read(1)  # delimiter line
        #print resp_plain, '\n', '1' * 20
        yield resp_plain, req_size


def parse_answ(answ_fh):
    stat = Statistic()
    for resp, size in answ_parser(answ_fh):
        p = HttpParser()
        p.execute(resp, int(size))
        stat.add_responce(p, resp)
    stat.represent()


def phout(phout_fh):
    result = []
    current_epoch = 0
    rps = 0
    for l in phout_fh:
        l_spltd = l.split()
        # in phantom v.14 line have 12 fields, @see:
        # http://phantom-doc-ru.rtfd.org/en/latest/analyzing_result_data.html
        if len(l_spltd) != 12:
            print 'Malformed line in phout file: %s' % l
        epoch, tag, rtt, con_ms, send_ms, proc_ms, resp_ms, phantom_exec, req_byte, resp_byte, errno, http_status = l_spltd
        epoch = int(epoch.split('.')[0])
        if epoch > current_epoch:
            result.append((current_epoch, rps))
            current_epoch = epoch
            rps = 0
        else:
            rps += 1

        #print l.rstrip()
        #print l_spltd
    print result

if __name__ == '__main__':
    parse_answ()
