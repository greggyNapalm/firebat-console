#!/usr/bin/env python
# -*- coding: utf-8 -*-


import os
import sys
import logging


from firebat.console.stepper import parse_ammo, process_load_schema, const_shema 
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
    #SCHEMA = 'line(2,11,1m)'
    SCHEMA = 'line(1001,1011,1m)'
    #SCHEMA = 'step(1,10,1,1m)'
    #SCHEMA = {'type': 'step', 'from':1, 'to':10, 'step_dur':2 }
    AMMO_PATH = './test.ammo'

    try:
        for tick in process_load_schema(SCHEMA, 0):
            sys.stdout.write(str(tick) + '\n')
            #print t_stamp,
            #print t_stamp
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

    #for t in const_shema(2, 0, 5000):
    #for t in const_shema(2, 10000, 5000):
    #    print t

    logger.debug('Job done.')

if __name__ == '__main__':
    main()
