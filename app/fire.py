#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
firebat.console
~~~~~~~~~~~~~~~

Helper script for Phantom load tool.
    * generate config files and input data.
    * runs test.
    * aggregate result data.
"""

import sys
import argparse

from configobj import ConfigObj, ConfigObjError

from conf import make_conf 

def exit_err(msg):
    sys.stderr.write(msg)
    sys.exit(1)


def main():
    # d
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    #
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--config', nargs=1, action='store',
                    dest='config_file', default='./fire.conf',
                    help='path to configuration file',)

    parser.add_argument('--debug', action="store_const", const=True,
            help='Whether to show debug msg in STDOUT', dest='debug')

    parser.add_argument('--version', action='version',
                    version='%(prog)s 0.0.1')
    args = parser.parse_args()

    try:
        config = ConfigObj(args.config_file, file_error=True)
    except IOError, e:
        exit_err('Could not read "%s": %s\n' % (args.config_file, e))
    except ConfigObjError, e:
        exit_err('Could not parse config file "%s": %s\n' %\
                 (args.config_file, e))

    #pp.pprint(config.__dict__)    
    #print config['title']['task']
    for f in config['fire']:
        print make_conf(config['fire'][f])
    print 'Done.'

if __name__ == '__main__':
    main()
