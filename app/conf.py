# -*- coding: utf-8 -*-

"""
firebat.conf
~~~~~~~~~~~~~~~

Helper script for Phantom load tool.
    * generate phantom.conf
"""

from jinja2 import Template

def make_conf(fire_cfg):
    # d
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(fire_cfg)
    #
    fire_cfg['modules'] = [
                            'io_benchmark',
                            'io_benchmark_method_stream',
                            'io_benchmark_method_stream_source_log',
                            'io_benchmark_method_stream_proto_http',
                        ]
    if fire_cfg['network_proto'] == 'ipv4':
        fire_cfg['modules'].append('io_benchmark_method_stream_ipv4')
    elif fire_cfg['network_proto'] == 'ipv6':
        fire_cfg['modules'].append('io_benchmark_method_stream_ipv6')
    else:
        raise NameError('Incorrent \'network_proto\' option in: \'%s\'' %\
                        fire_cfg['name'])

    if fire_cfg['transport_proto'] == 'ssl':
        fire_cfg['ssl_enabled'] = True
        fire_cfg['modules'].append('ssl')
        fire_cfg['modules'].append('io_benchmark_method_stream_transport_ssl')

    fire_cfg['target_ip_addr'] = '127.0.0.1'
    fire_cfg['target_tcp_port'] = '8080'
    

    try:
        with open('phantom_cfg/phantom.conf.tmpl', 'r') as f:
            phantom_cfg_tmlp = f.read()
            f.closed
    except IOError, e:
        print 'Can\'t open file: %s' % e
        return False
    template = Template(phantom_cfg_tmlp)
    return template.render(fire_cfg)
