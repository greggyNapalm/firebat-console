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
from datetime import date, datetime
import argparse
import logging
import getpass

from configobj import ConfigObj, ConfigObjError

from conf import make_conf 

def exit_err(msg):
    logger = logging.getLogger('firebat.console')
    logger.error(msg)
    if not logger.handlers:
        sys.stderr.write(msg)
    sys.exit(1)


def __build_path(config, fire_name, time):
    test_path = './run/'
    test_path += getpass.getuser() + '/'
    test_path += config['title']['task'] + '/'
    test_path += time.strftime('%Y%m%d-%H%M%S') + '/'
    test_path +=  fire_name
    return test_path


def main():
    TESTS_PATH = './run'
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


    logger = logging.getLogger('firebat.console')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    if args.debug:
        ch.setLevel(logging.DEBUG)
    else:
        ch.setLevel(logging.ERROR)
    formatter = logging.Formatter('%(asctime)s  %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    try:
        config = ConfigObj(args.config_file, file_error=True)
    except IOError, e:
        exit_err('Could not read "%s": %s\n' % (args.config_file, e))
    except ConfigObjError, e:
        exit_err('Could not parse config file "%s": %s\n' %\
                 (args.config_file, e))

    now = datetime.now()
    for f in config['fire']:
        path = __build_path(config, f, now)
        #if not os.path.exists(path):
        #    os.makedirs(path)
        
        #os.makedirs(TESTS_PATH + '/' + )
        make_conf(config['fire'][f])
    #print 'Done.'
    logger.debug('Job done.')

if __name__ == '__main__':
    main()
