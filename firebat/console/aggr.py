# -*- coding: utf-8 -*-

"""
firebat.agr
~~~~~~~~~~~

Aggregate test results.
"""

import os
import sys
import string
import datetime
import logging
from BaseHTTPServer import BaseHTTPRequestHandler as rh
import pprint
pp = pprint.PrettyPrinter(indent=4)

import simplejson as json
from simplejson.decoder import JSONDecodeError

from firebat.console.stepper import series_from_schema, schema_format_err


class phout_stat(object):
    def __init__(self, fire):
        #self.check = 0
        self.first_epoach = 0.0
        self.last_epoach = 0.0
        self.parts = [100, 99, 98, 95, 90, 85, 80, 75, 50]
        self.resp = {}
        #__vals = [[]] * len(self.parts)
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
        try:
            self.time_periods = fire['time_periods']
        except KeyError:
            exit_err('Can\'t parse *time_periods* fire attribute, it\'s ' +
                     'necessary!')
        for indx, bound in enumerate(self.time_periods):
            self.time_periods[indx] = bound_to_ms(str(bound),
                                                  self.time_periods)
        self.time_periods.sort()
        self.boundaries = {k: {'num': 0, 'percentil': 0} for k in\
                self.time_periods}
        self.responses_num = 0.0
        self.http_codes_num = 0.0
        self.reply_series = {
            'name': 'rps',
            'data': [],
        }
        self.resp_perc = []

    def add_resp(self, epoch, rtt, http_status, errno):
        '''Process regular log line.
        Args:
            epoch: int, time stamp.
            rtt: int, request round trip time.
            http_status: int, responce HTTP status code.
            errno: str, errno code from TCP socket.

        Returns:
            nothing, just update obj attributes
        '''
        rtt_ms = rtt / 1000
        self.responses_num += 1
        periods = self.time_periods[:]
        periods.append(rtt_ms)
        periods.sort()
        indx = periods.index(rtt_ms)
        try:
            self.boundaries[periods[indx + 1]]['num'] += 1
        except IndexError:
            exit_err('Buggy indx: %s\nperiods: %s in resp' % (indx, periods))
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

    def calc_percentiles(self, scrend_out_stmps):
        '''Aggregate added responces data.
            * resp time percentiles
            * HTTP status codes
            * Errno codes
        Args:
            scrend_out_stmps: time stamps will be used in charts.

        Returns:
            nothing, just update obj attributes
        '''
        # agregation pre requirements
        self.codes_lst = set(self.codes_lst)
        for c in self.codes_lst:
            self.codes_series[c] = []
        self.errno_lst = set(self.errno_lst)
        for e in self.errno_lst:
            self.errno_series[e] = []
        for tick, r in self.resp.iteritems():
            if tick in scrend_out_stmps:
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
                    try:
                        self.errno_series[e].append((tick,
                                                     r['errno'].get(e, 0)))
                    except KeyError:
                        self.errno_series[e] = [(tick, r['errno'].get(e, 0))]

    def get_errno_hcds(self):
        '''Make highcharts data series for errno chart.
        Returns:
            result: list of dicts
        '''
        result = []
        for errno_name, series in self.errno_series.iteritems():
            result.append({
                'name': errno_name,
                'data': series,
            })
        return result

    def get_status_codes_hcds(self):
        '''Make highcharts data series for HTTP status codes chart.
        Returns:
            result: list of dicts
        '''
        status_codes_series = []
        for key, val in self.codes_series.iteritems():
            status_codes_series.append({
                'name': key,
                'data': val,
            })
        return status_codes_series

    def calc_time_period_tbl(self):
    # time for period table
        prev = {
            'val': 0,
            'key': 0,
        }
        for key in sorted(self.boundaries.iterkeys()):
            self.boundaries[key]['percentil'] = round(\
                (self.boundaries[key]['num'] / self.responses_num) * 100, 2)
            self.boundaries[key]['btw'] = '%s -- %s' % (prev['key'], key)
            prev['val'] = round(self.boundaries[key]['percentil'] +\
                prev['val'], 2)
            self.boundaries[key]['perc_above'] = prev['val']
            prev['key'] = key

    def calc_codes_tbl(self):
        # HTTP status codes table
        for idx, val in self.codes_tbl.iteritems():
            val['percentil'] = round((val['num'] / self.http_codes_num) * 100,
                                     2)

    def calc_errno_tbl(self):
        # Errno table
        for idx, val in self.errno_tbl.iteritems():
            val['percentil'] = round((val['num'] / self.responses_num) * 100,
                                     2)

    def get_resp_perc_hcds(self):
        '''Make highcharts data series for resp time percentiles chart.
        Returns:
            result: list of dicts
        '''
        resp_perc = []
        self.series['1'] = self.series.pop('rps')  # to sort dict keys as ints
        for key in sorted(self.series.iterkeys(), key=lambda key: int(key),
                          reverse=True):
            if key == '1':
                self.reply_series['data'] = self.series[key]
                del self.series[key]
            else:
                name = key
                resp_perc.append({
                    'name': name,
                    'data': self.series[key],
            })
        return resp_perc


def exit_err(msg):
    logger = logging.getLogger('firebat.console')
    if isinstance(msg, str):
        msg = [msg, ]
    for m in msg:
        logger.error(m)
    if not logger.handlers:
        sys.stderr.write(msg)
    sys.exit(1)


def get_fire(json_path='.fire_up.json'):
    '''Read JSON encoded file with fire dict inside.
    Args:
        json_path: file path

    Returns:
        fire: dict, describes fire(job) options.
    '''

    try:
        with open(json_path, 'r') as fire_fh:
            return json.loads(fire_fh.read())
    except IOError, e:
        exit_err('Could not read "%s": %s\n' % (json_path, e))
    except JSONDecodeError, e:
        exit_err('Could not parse fire config file: %s\n%s' % (json_path, e))


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


def bound_to_ms(bound, time_periods):
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
    '''Calculate theoretical request per second sequinse.
    Args:
        fire: dict, current fire(job) options.

    Returns:
        result: list of tuples.
    '''
    result = []
    try:
        offset = int(fire['started_at'])
    except TypeError:
        exit_err('Can\'t parse fire *started_at* attribute, config malformed.')

    for schema in fire['load']:
        __series = series_from_schema(schema, offset)
        result.extend(__series)
        offset = __series[-1][0] + 1
    return result


def output_data(stat, calc_load_series, series_path='data_series.js'):
    ''' Write JS file with charts data series inside.
    Args:
        stat: obj, phout_stat instance.
        calc_load_series: list, theoretical rps sequinse.
        series_path: result file path.
    Returns:
        nothing, just write the file.
    '''

    # debug ticks
    #resp_prc = stat.get_resp_perc_hcds()
    #codes = stat.get_status_codes_hcds()
    #errno = stat.get_errno_hcds()
    #num = 22
    #print '   rps: %s' % calc_load_series['data'][num][0]
    #for i in range (9):
    #    print ' perc%s: %s' % (i, resp_prc[i]['data'][num][0])

    #for i in range (8):
    #    #print 'codes%s: %s' % (i, codes[i]['data'][num])
    #    print 'codes%s: %s' % (i, codes[i]['data'][num][0])

    #for i in range (2):
    #    print 'errno%s: %s' % (i, errno[i]['data'][num][0])

    with open(series_path, 'w+') as ds_fh:
        ds_fh.write('rps_series = ' + json.dumps(calc_load_series) + ';\n')
        #ds_fh.write('reply_series = ' + json.dumps(rps_series,
        #    indent=4 * ' ') + ';\n')
        ds_fh.write('resp_percentiles_series = ' +\
                json.dumps(stat.get_resp_perc_hcds()) + ';\n')
        ds_fh.write('status_codes_series = ' +\
                json.dumps(stat.get_status_codes_hcds()) + ';\n')
        ds_fh.write('errno_series = ' +\
                json.dumps(stat.get_errno_hcds()) + ';\n')


def get_pages_context(stat, fire):
    ctx = {}
    ctx['tgt_addr'] = fire.get('addr')
    ctx['load'] = fire['load']
    ctx['tags'] = fire.get('tag')

    started_at = datetime.datetime.fromtimestamp(float(fire['started_at']))
    ended_at = datetime.datetime.fromtimestamp(stat.last_epoach)
    ctx['date'] = started_at.strftime('%d %B %Y')
    ctx['from'] = started_at.strftime('%H:%M:%S')
    ctx['to'] = ended_at.strftime('%H:%M:%S')
    ctx['duration'] = str(ended_at - started_at)

    if fire.get('owner') == 'uid':
        ctx['owner'] = fire.get('uid')
    else:
        ctx['owner'] = fire.get('owner')

    # TODO: add to daemon fire update func
    ctx['src_host'] = fire.get('src_host')

    stat.calc_time_period_tbl()
    ctx['boundaries'] = stat.boundaries

    stat.calc_errno_tbl()
    for code, value in stat.errno_tbl.iteritems():
        value['msg'] = os.strerror(int(code))
    ctx['errno_tbl'] = stat.errno_tbl

    stat.calc_codes_tbl()
    for code, value in stat.codes_tbl.iteritems():
        value['msg'] = rh.responses.get(int(code), None)
        if value['msg']:
            value['msg'] = value['msg'][0]

    ctx['codes_tbl'] = stat.codes_tbl
    return ctx


def process_phout(phout_fh, points_num=200, dst_file='data_series.js',
                  fire_path='.fire_up.json'):
    ''' Read phout fire log, aggregate data, create charts data series.
    Args:
        phout_fh: File object with log data.
    Returns:
        static Web app on file system.
    '''

    fire = get_fire(json_path=fire_path)
    calc_load_series = {  # rps calculated data series
        'name': 'rps',
        'data': get_calc_load_series(fire),
    }
    # get only some points according to points_num value
    if points_num < len(calc_load_series['data']):
        step_size = int(len(calc_load_series['data']) / points_num)
        calc_load_series['data'] = calc_load_series['data'][0::step_size]

    scrend_out_stmps = [el[0] for el in calc_load_series['data']]

    p_stat = phout_stat(fire)
    current_epoch = 0
    for l in phout_fh:
        l_spltd = l.split()
        # in phantom v.14 line have 12 fields, @see:
        # http://phantom-doc-ru.rtfd.org/en/latest/analyzing_result_data.html
        if len(l_spltd) != 12:
            print 'Malformed line in phout file: %s' % l
        epoch, tag, rtt, con_ms, send_ms, proc_ms, resp_ms, phantom_exec, \
            req_byte, resp_byte, errno, http_status = l_spltd
        epoch = int(epoch.split('.')[0])  # cut out fractional part of epoach
        if epoch > current_epoch:
            if current_epoch == 0:
                p_stat.first_epoach = epoch
            current_epoch = epoch
            p_stat.last_epoach = epoch
        p_stat.add_resp(int(current_epoch), int(rtt), int(http_status), errno)

    # all phout lines parsed, time to aggregate data to expected metrics
    p_stat.calc_percentiles(scrend_out_stmps)
    output_data(p_stat, calc_load_series, series_path=dst_file)

    return get_pages_context(p_stat, fire)
