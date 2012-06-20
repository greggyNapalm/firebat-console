#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import logging


from firebat.console.stepper import parse_ammo, dec_load_schema
from firebat.console.exceptions import StepperAmmoFormat, StepperSchemaFormat


def main():
    #d
    import pprint
    pp = pprint.PrettyPrinter(indent=4)
    #d
    logger = logging.getLogger('firebat.console')
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s  %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    #SCHEMA = 'const(5,2m)'
    SCHEMA = 'line(1,11,1m)'
    AMMO_PATH = './test.ammo'

    try:
        for t_stamp in dec_load_schema(SCHEMA):
            print t_stamp
    except StepperSchemaFormat, e:
        logger.error('Error in load schema format: \'%s\'' % e.value['schema'])
        logger.error(e.value['msg'])

    #with open(AMMO_PATH, 'rb') as ammo_fh:
    #    try:
    #        for req in parse_ammo(ammo_fh):
    #            sys.stdout.write('+++\n')
    #            sys.stdout.write(req % 555)
    #    except StepperAmmoFormat, e:
    #        logger.error('Error in ammo file: %s' % e.value['file_path'])
    #        logger.error('At byte possition: %s' % e.value['byte_offset'])
    #        logger.error('Line looks like: \'%s\'' % e.value['err_line'])

    logger.debug('Job done.')

if __name__ == '__main__':
    main()
