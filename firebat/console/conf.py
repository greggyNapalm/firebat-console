# -*- coding: utf-8 -*-

"""
firebat.conf
~~~~~~~~~~~~~~~

Helper script for Phantom load tool.
    * generate phantom.conf
"""

import os
import sys
import re
import socket
import logging

from jinja2 import Template
import yaml


def exit_err(msg):
    logger = logging.getLogger('firebat.console')
    if isinstance(msg, str):
        msg = [msg, ]
    for m in msg:
        if not logger.handlers:
            sys.stderr.write(m)
        else:
            logger.error(m)
    sys.exit(1)


def make_conf(fire_cfg, **kwargs):
    """ Generate ready to use phantom.conf
    Args:
        fire_cfg: dict with fire configuration

    Returns:
        str with phantom.conf inside
    """
    logger = logging.getLogger('firebat.console')
    conf = {
        'network_proto': 'ipv4',
        'transport_proto': 'tcp',
        'lib_dir': '/usr/lib/phantom',
        'modules': [
            'io_benchmark',
            'io_benchmark_method_stream',
            'io_benchmark_method_stream_source_log',
            'io_benchmark_method_stream_proto_http',
        ],
        'scheduler': {
            'threads': 13,
            'event_buf_size': 20,
            'timeout_prec': 1,
        },
        'answ_log': {
            'path': 'answ.txt',
            'level': 'all',
        },
        'phout_log': {
            'path': 'phout.txt',
            'time_format': 'unix',
        },
        'ammo_path': 'ammo.stpd',
        'target_timeout': '10s',
        'stat_log_path': 'phantom_stat.log',
        'times': {
            'max': '1s',
            'min': '10',
            'steps': '20',
        },

    }
    conf.update(fire_cfg)
    conf.update(kwargs)

    if conf['network_proto'] == 'ipv4':
        conf['modules'].append('io_benchmark_method_stream_ipv4')
        # We need validate addr first
        if ':' in conf['addr']:
            addr, port = conf['addr'].split(':')
        else:
            addr, port = conf['addr'], ''
        ip_addr_regex = '^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$'
        if re.match(ip_addr_regex, addr):
            conf['target_ip_addr'] = addr
            conf['target_tcp_port'] = port
        else:
            try:
                conf['target_ip_addr'] = socket.gethostbyname(addr)
                conf['target_tcp_port'] = port
            except socket.gaierror, e:
                __msg = 'Can\'t resolve domain name: %s; \'%s\' > \'%s\'' % \
                        (addr, conf['name'], conf['addr'])
                logger.error(__msg)
    elif conf['network_proto'] == 'ipv6':
        conf['modules'].append('io_benchmark_method_stream_ipv6')
        # TODO: validation for ipv6 addr
        if ':' in conf['addr']:
            addr, port = conf['addr'].split(':')
        else:
            addr, port = conf['addr'], ''
        conf['target_ip_addr'] = addr
        conf['target_tcp_port'] = port
    else:
        __msg = 'Incorrent config option: \'%s\' > \'network_proto\'' % conf['name']
        logger.error(__msg)
        raise NameError(__msg)

    if conf['transport_proto'] == 'ssl':
        conf['ssl_enabled'] = True
        conf['modules'].append('ssl')
        conf['modules'].append('io_benchmark_method_stream_transport_ssl')

    tmpl_path = os.path.dirname(__file__) + '/phantom.conf.jinja'
    try:
        with open(tmpl_path, 'r') as f:
            phantom_cfg_tmlp = f.read()
            f.closed
    except IOError, e:
        __msg = 'Can\'t open cfg template file: %s' % e
        logger.error(__msg)
        return False
    template = Template(phantom_cfg_tmlp)
    return template.render(conf)


def get_defaults():
    defaults_conf_path = os.path.dirname(__file__) + '/defaults.yaml'
    try:
        with open(defaults_conf_path, 'r') as conf_fh:
            config = yaml.load(conf_fh)
    except IOError, e:
        exit_err('Could not read "%s": %s\n' % (defaults_conf_path, e))
    except yaml.scanner.ScannerError, e:
        exit_err('Could not parse *defaults* config file: %s\n%s' %\
                (defaults_conf_path, e))
    return config
