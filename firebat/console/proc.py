#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
firebat.proc
~~~~~~~~~~~~~~~

Contain functions for build tests:
    * Compile Phantom input data
    * Run tests
"""

import os
import datetime
import getpass
import cPickle
import commands
import itertools
import logging
import copy
import base64
import gzip
from progressbar import Bar, ProgressBar, Percentage, ETA
import pprint
pp = pprint.PrettyPrinter(indent=4)

import simplejson as json
import validictory

from firebat.console.conf import make_p_conf
from firebat.console.stepper import parse_ammo, process_load_schema
from firebat.console.stepper import fire_duration
from firebat.console.helpers import validate, fetch_from_armorer
from exceptions import StepperSchemaFormat, FireEmergencyExit


def build_path(orig_wd, test_cfg, fire_cfg, time):
    '''Create str with path fo fire based on test config.
    '''
    test_id = test_cfg.get('id', None)
    if test_id:
        test_wd = '%s/%s' % (orig_wd, test_id)
    else:
        test_wd = orig_wd + '/'
        test_wd += test_cfg['title']['task'] + '_'
        test_wd += getpass.getuser() + '_'
        test_wd += time.strftime('%Y%m%d-%H%M%S')

    #if os.path.exists(test_wd):
    #    raise FireEmergencyExit('Test working directory allready exist: %s' %\
    #                            test_wd)

    fire_id = fire_cfg.get('id', None)
    if fire_id:
        fire_wd = '%s-%s' % (fire_id, fire_cfg['name'])
    else:
        fire_wd = fire_cfg['name']

    return '%s/%s' % (test_wd, fire_wd)


def get_ammo(test_cfg, arm_api_url='http://armorer.load.io'):
    '''Ammo providers API wrapper.
    Args:
        test_cfg: dict, test config.
        armorer_api: str, REST API base url.

    Returns:
        test_cfg: dict, updated test config.
    '''
    #logger = logging.getLogger('root')

    pref = ''
    if test_cfg['ammo']['type'] == 'armorer':
        pref = 'armorer/'
        ammo_url = test_cfg['ammo']['source']
        local_ammo_path = fetch_from_armorer(ammo_url,
                                            api_url=arm_api_url)

    if not local_ammo_path:
        pass

    if not os.path.exists(pref):
        os.makedirs(pref)

    if test_cfg['ammo']['method'] in ['round-robin', 'rr']:
        parts = len(test_cfg['fire'])

        ammo_fhs = []
        for idx in range(parts):
            try:
                ammo_fhs.append(open('%s%s.qs' % (pref, idx), 'w+'))
            except IOError, e:
                return False, 'Can\'t create ammo file: %s' % e

        ammo_fhs_it = itertools.cycle(ammo_fhs)
        with gzip.open(local_ammo_path, 'r') as gz_fh:
            for line in gz_fh:
                cur_ammo_fh = ammo_fhs_it.next()
                cur_ammo_fh.write(line)

        for idx, fh in enumerate(ammo_fhs):
            test_cfg['fire'][idx]['input_file'] = os.path.abspath(fh.name)
            test_cfg['fire'][idx]['input_format'] = 'qs'
            fh.close()

    return test_cfg


def start_daemon(fire):
    ''' Build cmd string for system start-stop-daemon tool and call it.
    Args:
        fire: dict, fire from job configuration.

    Returns:
        status_d: int, command exit code.
        text_d: str, command stdout.
    '''
    exec_name = 'daemon_fire'
    status, exec_path = commands.getstatusoutput('which %s' % exec_name)
    if status != 0:
        raise ValueError('Can\'t find executable: %s' % exec_name)

    opts = {
        'id': fire.get('id', None),
        'owner': fire.get('owner', 'uid'),
        'total_dur': fire['total_dur'] / 1000,  # in seconds
    }
    if 'autostop' in fire:
        opts['autostop'] = fire['autostop']
    opts_str = base64.b64encode(cPickle.dumps(opts))

    cmd = 'start-stop-daemon --start --quiet --background'
    cmd += ' --pidfile /None_existent'
    cmd += ' --chdir %s' % fire['wd']
    cmd += ' --exec %s -- %s' % (exec_path, opts_str)

    status_d, text_d = commands.getstatusoutput(cmd)
    return status_d, text_d


def build_test(test_cfg, args=None):
    '''Create dirs tree, phantom.cfg and ammo.stpd
    Args:
        test_cfg: dict, test config.
        default: dict, default settings and validation rules.
        args: argparse obj instance.
    '''
    logger = logging.getLogger('root')

    now = datetime.datetime.now()
    orig_wd = os.getcwd()
    ammo_from_arg = False
    test_http_cntx = None
    if 'ammo' in test_cfg:
        test_http_cntx = test_cfg['ammo'].get('http_context', None)

    for idx, f in enumerate(test_cfg['fire']):
        try:
            validate(f, tgt='fire')
        except validictory.validator.ValidationError, e:
            raise FireEmergencyExit('Error in parsing fire dict:\n%s' % e)

        # get absolute ammo path before chdir
        if not ammo_from_arg:
            if args and args.ammo_file:
                ammo_from_arg = os.path.abspath(args.ammo_file)
                ammo_path = ammo_from_arg
            else:
                ammo_path = f['input_file']

        if not os.path.isfile(ammo_path):
            raise FireEmergencyExit('No such ammo file: %s' % ammo_path)

        try:
            pbar_max = f['total_dur'] = fire_duration(f)
        except StepperSchemaFormat, e:
            msg = [
                'Malformed shcema format in fire: %s' % f['name'],
                'in \'%s\' > \'%s\'' % (f['name'], e.value['schema'])
            ]
            raise FireEmergencyExit(msg)

        widgets = [Percentage(), Bar(), ETA(), ]
        pbar = ProgressBar(widgets=widgets, maxval=pbar_max).start()

        # create working directory for fire(jobs) and chdir to it.
        f['wd'] = build_path(orig_wd, test_cfg, f, now)
        test_cfg['fire'][idx] = copy.copy(f)
        os.makedirs(f['wd'])
        os.chdir(f['wd'])

        fire_json = json.dumps(test_cfg['fire'][idx], indent=4 * ' ')
        with open('.fire.json', 'w+') as fire_fh:
            fire_fh.write(fire_json)

        with open('phantom.conf', 'w+') as cfg_fh:
            phantom_cfg = make_p_conf(f)
            if phantom_cfg:
                cfg_fh.write(phantom_cfg)
            else:
                raise FireEmergencyExit(
                        'Can\'t create phantom.cfg from fire dict.')

        logger.info('Processing fire: %s' % f['name'])
        logger.info('Ammo file: %s' % ammo_path)
        logger.info('Load schema: %s' % f['load'])
        stpd_start = datetime.datetime.now()

        with open(ammo_path, 'r') as ammo_fh,\
            open('ammo.stpd', 'w+') as stpd_fh:
            try:
                gen_ammo = parse_ammo(ammo_fh, f,
                                      test_http_cntx=test_http_cntx)
            except ValueError, e:
                raise FireEmergencyExit('Can\'t parse ammo file', e)
            offset = f.get('offset', 0)
            for schema in f['load']:
                for tick in process_load_schema(schema, offset):
                    try:
                        m_line, chunk = gen_ammo.next()
                    except StopIteration:
                        # chunks in ammo file run out
                        if f['loop_ammo']:
                            # need to restart requests chunks generator
                            ammo_fh.seek(0)
                            gen_ammo = parse_ammo(ammo_fh, f,
                                                 test_http_cntx=test_http_cntx)
                            m_line, chunk = gen_ammo.next()
                        else:
                            stpd_fh.write('0')
                            msg = [
                                'Not enough requests in ammo file' +
                                ' to cover load schema.',
                                'File: %s' % f['input_file'],
                                'Schema: %s' % schema,
                            ]
                            logger.info(msg)
                            break
                    req_stpd = m_line % tick + chunk + '\n'
                    stpd_fh.write(req_stpd)
                    pbar.update(tick)
                offset = tick  # use last time tick as next load schema offset
            stpd_fh.write('0')  # close stpd file according to format
        pbar.finish()
        stpd_stop = datetime.datetime.now()
        stpd_job_dur = stpd_stop - stpd_start
        logger.debug('ammo job takes: %s\n' % stpd_job_dur)
    logger.info('stpd generation finished.')
