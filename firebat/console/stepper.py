# -*- coding: utf-8 -*-

"""
firebat.stepper
~~~~~~~~~~~~~~~

Generate stepped ammo(input data + load schema)
"""

import os
import string
import logging

from exceptions import StepperAmmoFormat, StepperSchemaFormat


def parse_ammo(ammo_fh):
    '''Validate and reformat input requests data(ammo file)
    Args:
        ammo_fh: File object, content in lunapark ammo format

    Returns:
        generator, which yield str with placeholder for timestamp
    '''
    def __file_format_err(ammo_fh, line):
        except_data = {}
        except_data['msg'] = 'Wrong metadata line format'
        except_data['file_path'] = os.path.abspath(ammo_fh.name)
        except_data['byte_offset'] = ammo_fh.tell()
        except_data['err_line'] = line
        raise StepperAmmoFormat(except_data)

    while True:
        raw_line = ammo_fh.readline()
        line_spltd = raw_line.split()
        if len(line_spltd) == 2:
            # meta line with size and tag
            line_form = line_spltd[0] + ' %s ' + line_spltd[1] + '\n'
        elif len(line_spltd) == 1:
            # meta line with size only
            line_form = line_spltd[0] + ' %s' + '\n'
        else:
            __file_format_err(ammo_fh, raw_line.rstrip())

        if not line_spltd[0].isdigit():
            __file_format_err(ammo_fh, raw_line.rstrip())
        if line_spltd[0] == '0':
            # We reached EOF
            break

        chunk = ammo_fh.read(int(line_spltd[0]))
        yield line_form + chunk


def dec_load_schema(schema):
    '''Make time ticks from load schema(lunapark format)
    Args:
        schema: str, @see docs #FIXME: add docs link

    Returns:
        generator, which yield int - time tick in milliseconds from test start
    '''

    def __validate_duration(duration):
        '''Check conformity of short notation
        Args:
            duration: str with declare time interval in short notation

        Returns:
            bool, true if short notation is valid
        '''
        trans_table = string.maketrans('', '')
        allowed = string.digits + 'smh'
        return not duration.translate(trans_table, allowed)

    def __trans_to_ms(duration):
        '''Transfer duration from short notation to milliseconds
        Args:
            duration: str with declare time interval in short notation

        Returns:
            int, time interval in milliseconds
        '''
        if duration.endswith('m'):
            duration = int(duration.rstrip('m')) * 60
        elif duration.endswith('h'):
            duration = int(duration.rstrip('h')) * 60 ** 2
        return duration * 10 ** 3

    def __schema_format_err(schema, msg=None):
        except_data = {}
        except_data['msg'] = 'Wrong schema format'
        except_data['schema'] = schema
        if msg:
            except_data['msg'] += msg
        raise StepperSchemaFormat(except_data)


    if schema.startswith('line'):
        schema = schema.strip('line(').rstrip(')')
        rps_from, rps_to, duration = schema.split(',')
        if not (rps_from.isdigit() and rps_to.isdigit() and\
                __validate_duration(duration)):
            __schema_format_err(schema)

        duration = __trans_to_ms(duration)
        print 'line', rps_from, rps_to, duration
        step_duration = duration / float(rps_to)
        step_val = 1
        print 'step_duration: %s' % step_duration
        timestamp = 0
        while timestamp < duration:
            yield timestamp
            timestamp += step_duration

    elif schema.startswith('const'):
        schema = schema.strip('const(').rstrip(')')
        rps, duration = schema.split(',')
        if not (rps.isdigit() and __validate_duration(duration)):
            __schema_format_err(schema)

        duration = __trans_to_ms(duration)
        print 'const', rps, duration
        delay = 1000 / int(rps)
        timestamp = -delay
        while timestamp < duration - delay:
            timestamp += delay
            yield timestamp
    elif schema.startswith('step'):
        pass
    else:
        __schema_format_err(schema, msg=', Can\'t determine schema type')
