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
import bisect
import rbtree
from subprocess import Popen, PIPE

from jinja2 import Template
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


class phout_stat(object):
    def __init__(self):
        self.parts = [100, 99, 98, 95, 90, 85, 80, 75, 50]
        self.resp = {}
        self.series = {
            'rps': '',
            '100': '',
            '99': '',
            '98': '',
            '95': '',
            '90': '',
            '85': '',
            '80': '',
            '75': '',
            '50': '',
        }

    def add_resp(self, epoch, rtt):
        try:
            self.resp[epoch]['rtt'].append(rtt)
        except KeyError:
            self.resp[epoch] = {
                'percentiles': [],
                'rtt': [],
                'rps': 0,
            }
            self.resp[epoch]['rtt'].append(rtt)

    def calc_percentiles(self):
        for idx, r in self.resp.iteritems():
            r['rtt'].sort()
            r['rps'] = len(r['rtt'])
            for p in self.parts:
                if p == 100:
                    elem_no = -1
                else:
                    elem_no = int(r['rps'] *(p / 100.0))
                resp_time = r['rtt'][elem_no]
                r['percentiles'].append(resp_time)
                self.series[str(p)] += '[%s, %s],\n' % (idx, resp_time)
            self.series['rps'] += '[%s, %s],\n' % (idx, r['rps'])
                

def phout(phout_fh):
    p_stat = phout_stat()
    current_epoch = 0
    for l in phout_fh:
        l_spltd = l.split()
        # in phantom v.14 line have 12 fields, @see:
        # http://phantom-doc-ru.rtfd.org/en/latest/analyzing_result_data.html
        if len(l_spltd) != 12:
            print 'Malformed line in phout file: %s' % l
        epoch, tag, rtt, con_ms, send_ms, proc_ms, resp_ms, phantom_exec, req_byte, resp_byte, errno, http_status = l_spltd
        epoch = int(epoch.split('.')[0])
        if epoch > current_epoch:
            current_epoch = epoch
        else:
            p_stat.add_resp(int(current_epoch), int(rtt))

    p_stat.calc_percentiles()
    #pp.pprint(p_stat.series)
    #print p_stat.series['rps']

    header = 'data_series = [\n'
    footer = ']'
    with open('data_series.js', 'w+') as ds_fh:
        ds_fh.write(header)
        p_stat.series['101'] = p_stat.series.pop('rps')
        for key in sorted(p_stat.series.iterkeys(), key=lambda key: int(key), reverse=True):
            if key == '101':
                name = 'rps'
            else:
                name = key
            ds_fh.write('{\nname: \'%s\',\ndata: [\n' % name)
            ds_fh.write(p_stat.series[key])
            ds_fh.write(']\n}, ')
        ds_fh.write(footer)



if __name__ == '__main__':
    parse_answ()
