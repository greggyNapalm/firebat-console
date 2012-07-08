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
from simplejson.decoder import JSONDecodeError
import datetime
import bisect
import rbtree
import copy
from subprocess import Popen, PIPE

from jinja2 import Template
try:
    from http_parser.parser import HttpParser
except ImportError:
    from http_parser.pyparser import HttpParser

from firebat.console.stepper import series_from_schema
import string

#
import pprint
pp = pprint.PrettyPrinter(indent=4)

# constaints
POINTS_IN_CHART = 120.0
#POINTS_IN_CHART = 300.0


class phout_stat(object):
    def __init__(self, fire):
        self.check = 0
        self.first_epoach = 0
        self.last_epoach = 0
        self.parts = [100, 99, 98, 95, 90, 85, 80, 75, 50]
        self.resp = {}
        __vals = [[]] * len(self.parts)
        #self.series = dict(zip([str(e) for e in self.parts], __vals))
        #self.series['rps'] = []
        self.series = {
            'rps': [],
            '100': [],
            '99': [],
            '98': [],
            '95': [],
            '90': [],
            '85': [],
            '80': [],
            '75': [],
            '50': [],
        }
        self.codes_lst = []
        self.codes_series = {}
        self.codes_tbl = {}
        self.errno_lst = []
        self.errno_series = {}
        self.errno_tbl = {}
        self.time_periods = fire['time_periods']
        #self.schema = fire['load']
        for indx, bound in enumerate(self.time_periods):
            self.time_periods[indx] = bound_to_ms(str(bound), self.time_periods)
        self.time_periods.sort()
        self.boundaries = {k: {'num': 0, 'percentil': 0} for k in\
                self.time_periods}
        self.responses_num = 0.0
        self.http_codes_num = 0.0

    def add_resp(self, epoch, rtt, http_status, errno):
        rtt_ms = rtt / 1000
        self.responses_num += 1
        periods = self.time_periods[:]
        periods.append(rtt_ms)
        periods.sort()
        indx = periods.index(rtt_ms)
        try:
            self.boundaries[periods[indx + 1]]['num'] += 1
        except IndexError:
            print 'indx: %s\nperiods: %s' %(indx, periods)
        try:
            self.resp[epoch]['rtt'].append(rtt)
        except KeyError:
            self.resp[epoch] = {
                'percentiles': [],
                'rtt': [],
                'rps': 0,
                'codes': {},
                'errno': {},
            }
            self.resp[epoch]['rtt'].append(rtt)

        if http_status != 0:  # 0 mean transport layer error.
            self.http_codes_num += 1
            # HTTP status codes processing for each req
            try:
                self.resp[epoch]['codes'][http_status] += 1
            except KeyError:
                self.resp[epoch]['codes'][http_status] = 1
                self.codes_lst.append(http_status)

            # for all test
            try:
                self.codes_tbl[http_status]['num'] += 1
            except KeyError:
                self.codes_tbl[http_status] = {'num': 1}

        # Socket errno processing for each req
        try:
            self.resp[epoch]['errno'][errno] += 1
        except KeyError:
            self.resp[epoch]['errno'][errno] = 1
            self.errno_lst.append(errno)
        
        # for all test
        try:
            self.errno_tbl[errno]['num'] += 1
        except KeyError:
            self.errno_tbl[errno] = {'num': 1}

    def calc_percentiles(self):
        # agregation pre requirements
        step_size = int(len(self.resp.keys()) / POINTS_IN_CHART)
        for c in self.codes_lst:
            self.codes_series[c] = []
        for e in self.errno_lst:
            self.errno_series[e] = []
        #print 'step_size: %s' % step_size
        cntr = 0
        cur_epoch = 0
        for idx, r in self.resp.iteritems():
            if (cntr == step_size) or (idx == cur_epoch):
                cur_epoch = idx
                cntr = 0
                tick = idx * 1000  # java script time format
                self.check += 1

                # responce time calc
                r['rtt'].sort()
                r['rps'] = len(r['rtt'])
                for p in self.parts:
                    if p == 100:
                        elem_no = -1
                    else:
                        elem_no = int(r['rps'] * (p / 100.0))
                    resp_time = r['rtt'][elem_no]
                    r['percentiles'].append(resp_time)
                    # convers resp_time from microseconds to milliseconds
                    self.series[str(p)].append((tick, resp_time / 1000))
                self.series['rps'].append((tick, r['rps']))

                # status codes
                for c in self.codes_lst:
                    val = r['codes'].get(c, 0)
                    self.codes_series[c].append((tick, int(val)))

                # errno
                for e in self.errno_lst:
                    val = r['errno'].get(e, 0)
                    self.errno_series[e].append((tick, int(val)))
            else:
                cntr += 1


def get_fire(json_path='.fire_up.json'):
    try:
        with open(json_path, 'r') as fire_fh:
            return json.loads(fire_fh.read())
    except IOError, e:
        print 'Could not read "%s": %s\n' % (json_path, e)
    except JSONDecodeError, e:
        print 'Could not parse fire config file: %s\n%s' % (json_path, e)

def validate_bound(bound):
    '''Check conformity of bound short notation
    Args:
        bound: str with declare time bound in short notation

    Returns:
        bool, true if short notation is valid
    '''
    trans_table = string.maketrans('', '')
    allowed = string.digits + 'sm'
    return not bound.translate(trans_table, allowed)


def bound_to_ms(bound,time_periods):
    '''Transfer bound from short notation to milliseconds
    Args:
        bound: str with declare time bound in short notation

    Returns:
        int, time bound in milliseconds
    '''
    if not validate_bound(bound):
        schema_format_err(time_periods, msg=', Time periods malformed')
    if bound.endswith('s'):
        bound = int(bound.rstrip('s')) * 10 ** 3
    elif bound.endswith('m'):
        bound = int(bound.rstrip('m')) * 60 * 10 ** 3
    else:
        bound = int(bound)
    return bound


def get_calc_load_series(fire):
    result = []
    offset = int(fire['started_at'])
    for schema in fire['load']:
        __series = series_from_schema(schema, offset)
        result.extend(__series)
        # last tick of current series is offset for next series
        offset = (__series[-1][0] / 1000 ) + 1
    return result


def phout(phout_fh):
    fire = get_fire()
    #pp.pprint(fire)
    calc_load_series = {
        'name': 'rps',
        'data': get_calc_load_series(fire),
    }
    print len(calc_load_series['data'])
    step_size = int(len(calc_load_series['data']) / POINTS_IN_CHART)
    print 'step: %s' % step_size
    calc_load_series['data'] = calc_load_series['data'][0::step_size]
    print len(calc_load_series['data'])
    p_stat = phout_stat(fire)
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
            if current_epoch == 0:
                p_stat.first_epoach = epoch
            current_epoch = epoch
            p_stat.last_epoach = epoch
        p_stat.add_resp(int(current_epoch), int(rtt), int(http_status),
                            errno)

    p_stat.calc_percentiles()

    resp_perc = []
    rps_series = {
        'name': 'rps',
        'data': [],
    }
    p_stat.series['1'] = p_stat.series.pop('rps')
    for key in sorted(p_stat.series.iterkeys(), key=lambda key: int(key), reverse=True):
        if key == '1':
            rps_series['data'] = p_stat.series[key]
        else:
            name = key
            resp_perc.append({
                'name': name,
                'data': p_stat.series[key],
        })

    status_codes_series = []
    for key, val in p_stat.codes_series.iteritems():
        status_codes_series.append({
            'name': key,
            'data': val,
        })

    errno_series = []
    for key, val in p_stat.errno_series.iteritems():
        errno_series.append({
            'name': key,
            'data': val,
        })

    with open('data_series.js', 'w+') as ds_fh:
        ds_fh.write('rps_series = ' + json.dumps(calc_load_series,
            indent=4 * ' ') + ';\n')
        ds_fh.write('reply_series = ' + json.dumps(rps_series,
            indent=4 * ' ') + ';\n')
        ds_fh.write('resp_percentiles_series = ' + json.dumps(resp_perc,
            indent=4 * ' ') + ';\n')
        ds_fh.write('status_codes_series = ' + json.dumps(status_codes_series,
            indent=4 * ' ') + ';\n')
        ds_fh.write('errno_series = ' + json.dumps(errno_series,
            indent=4 * ' ') + ';\n')
    print 'Check: %s' % p_stat.check
    print '\nTotal:', p_stat.responses_num, '\n'


    prev = {
        'val': 0,
        'key': 0,
    }
    for key in sorted(p_stat.boundaries.iterkeys()):
        p_stat.boundaries[key]['percentil'] = round(\
            (p_stat.boundaries[key]['num'] / p_stat.responses_num) * 100, 2)
        p_stat.boundaries[key]['btw'] = '%s -- %s' % (prev['key'], key)
        prev['val'] = round(p_stat.boundaries[key]['percentil'] + prev['val'], 2)
        p_stat.boundaries[key]['perc_above'] = prev['val']
        prev['key'] = key

    #pp.pprint(p_stat.boundaries)

    for idx, val in p_stat.codes_tbl.iteritems():
        val['percentil'] = round((val['num'] / p_stat.http_codes_num) * 100, 2)
    pp.pprint(p_stat.codes_tbl)

    ctot = 0
    for idx, val in p_stat.errno_tbl.iteritems():
        val['percentil'] = round((val['num'] / p_stat.responses_num) * 100, 2)
        ctot += val['percentil']
    print ctot
    pp.pprint(p_stat.errno_tbl)


if __name__ == '__main__':
    parse_answ()
