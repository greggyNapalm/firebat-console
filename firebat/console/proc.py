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
import copy
import base64
from progressbar import Bar, ProgressBar, Percentage, ETA
import pprint
pp = pprint.PrettyPrinter(indent=4)

import simplejson as json

from firebat.console.conf import make_p_conf
from firebat.console.stepper import parse_ammo, process_load_schema
from firebat.console.stepper import fire_duration
from firebat.console.cmd import get_logger
from firebat.console.helpers import validate_dict, exit_err
from exceptions import StepperSchemaFormat


def build_path(orig_wd, config, fire, time):
    '''Create str with path fo fire based on current time and fire name.
    '''
    test_path = orig_wd + '/'
    test_path += config['title']['task'] + '_'
    test_path += getpass.getuser() + '_'
    test_path += time.strftime('%Y%m%d-%H%M%S') + '/'
    test_path += fire['name']
    return test_path


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


def build_test(cfg, defaults, args, logger=None):
    '''Create dirs tree, phantom.cfg and ammo.stpd
    Args:
        fire: dict, test config.
        default: dict, default settings and validation rules.
        args: argparse obj instance.
    '''
    if not logger.handlers:
        logger = get_logger()

    now = datetime.datetime.now()
    orig_wd = os.getcwd()
    ammo_from_arg = False

    for idx, f_orig in enumerate(cfg['fire']):
        f = defaults['fire_conf']
        f.update(f_orig)
        try:
            validate_dict(f, defaults['fire_required_keys'])
        except ValueError, e:
            exit_err('Error in parsing fire conf:\n%s' % e)

        # get absolute ammo path before chdir
        if not ammo_from_arg:
            if args.ammo_file:
                ammo_from_arg = os.path.abspath(args.ammo_file)
                ammo_path = ammo_from_arg
            else:
                ammo_path = f['input_file']

        if not os.path.isfile(ammo_path):
            exit_err('No such file: %s' % ammo_path)

        try:
            pbar_max = f['total_dur'] = fire_duration(f)
        except StepperSchemaFormat, e:
            msg = [
                'Malformed shcema format in fire: %s' % f['name'],
                'in \'%s\' > \'%s\'' % (f['name'], e.value['schema'])
            ]
            exit_err(msg)

        widgets = [Percentage(), Bar(), ETA(), ]
        pbar = ProgressBar(widgets=widgets, maxval=pbar_max).start()

        # create working directory for fire(jobs) and chdir to it.
        f['wd'] = build_path(orig_wd, cfg, f, now)
        cfg['fire'][idx] = copy.copy(f)
        os.makedirs(f['wd'])
        os.chdir(f['wd'])

        fire_json = json.dumps(cfg['fire'][idx], indent=4 * ' ')
        with open('.fire.json', 'w+') as fire_fh:
            fire_fh.write(fire_json)

        with open('phantom.conf', 'w+') as cfg_fh:
            phantom_cfg = make_p_conf(f)
            if phantom_cfg:
                cfg_fh.write(phantom_cfg)
            else:
                exit_err('Can\'t create phantom.cfg from fire dict.')

        logger.info('Processing fire: %s' % f['name'])
        logger.info('Ammo file: %s' % ammo_path)
        logger.info('Load schema: %s' % f['load'])
        stpd_start = datetime.datetime.now()

        with open(ammo_path, 'r') as ammo_fh,\
            open('ammo.stpd', 'w+') as stpd_fh:
            gen_ammo = parse_ammo(ammo_fh)
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
                            gen_ammo = parse_ammo(ammo_fh)
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
        logger.info('ammo job takes: %s\n' % stpd_job_dur)
    logger.info('stpd generation finished.')
