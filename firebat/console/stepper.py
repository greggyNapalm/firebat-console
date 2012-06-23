# -*- coding: utf-8 -*-

"""
firebat.stepper
~~~~~~~~~~~~~~~

Generate stepped ammo(input data + load schema)
"""

import os
import sys
import string
import logging

from exceptions import StepperAmmoFormat, StepperSchemaFormat


def schema_format_err(schema, msg=None):
    ''' Validate and reformat input requests data(ammo file)
    Args:
        schema: str, @ see doc for format
        msg : str, optional error description
    '''

    except_data = {}
    except_data['msg'] = 'Wrong schema format'
    except_data['schema'] = schema
    if msg:
        except_data['msg'] += msg
    raise StepperSchemaFormat(except_data)


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


def const_shema(rps, duration, tick_offset):
    '''Make time ticks from constraint load algorithm(load schema)
    Args:
        rps: float,request peer second
        duration: load chank duration
        tick_offset: int, first tick offset

    Returns:
        generator, which yield int time tick in milliseconds
    '''
    delay = 1000 / int(rps)
    tick = int(tick_offset) - delay
    last_tick = tick_offset + int(duration) - delay
    while tick < last_tick:
        tick += delay
        yield tick


def step_shema(rps_from, rps_to, step_dur, step_size, tick_offset):
    '''Make time ticks from step load algorithm(load schema)
    Args:
        rps_from: float, first step load(request peer second)
        rps_to: float, last step load(request peer second)
        step_dur: int, each step time length
        step_size: int, rps difference between two neighboring steps
        tick_offset: int, previous time tick position

    Returns:
        generator, which yield int time tick in milliseconds
    '''
    cur_step = rps_from
    cur_step_border = tick_offset
    while cur_step < rps_to:
        #print '\ncur_step: %s; step_dur: %s\n' %\
        #        (cur_step, step_dur)
        for tick in const_shema(cur_step, step_dur, cur_step_border):
            yield tick
        cur_step += step_size
        cur_step_border += step_dur
        #print 'border: %s' % cur_step_border


def line_shema(rps_from, rps_to, duration, tick_offset):
    '''Make time ticks from line load algorithm(load schema)
    Args:
        rps_from: float, starting load
        rps_to: float, ending load
        duration: int, time length in milliseconds
        tick_offset: int, previous time tick position

    Returns:
        generator obj, which yield int time tick in milliseconds
    '''
    der = ((rps_to - rps_from) / 1000.0) / duration  # load derivative
    ticks_in_ms = rps_from / 1000.0
    if ticks_in_ms < 1:
        proficit = 1.0
    up = 0.0  # inaccuracy, because request in millisecond is int, func linear

    for t in xrange(tick_offset, tick_offset + duration + 1):
        if ticks_in_ms > 1:
            #sys.stdout.write('+' * int(ticks_in_ms))
            for indx in int(ticks_in_ms):
                yield t
        else:
            proficit += ticks_in_ms
            if proficit > 1.0:
                yield t
                #sys.stdout.write('+')
                proficit -= 1.0
        load = (rps_from / 1000.0) + der * t

        up = up + load - ticks_in_ms
        deficit = up - 1.0
        if deficit > 0:
            yield t
            #sys.stdout.write('+')
            up = deficit

        if int(load - ticks_in_ms) >= 1:
            ticks_in_ms = int(load)

        #sys.stdout.write('t: %s; magic: %s; load: %s; up: %s;\
        #        tics: %s\n' % (t, der * t, load, up,
        #            ticks_in_ms))


def process_load_schema(schema, tick_offset):
    ''' Parse and validate load algorithm(load schema) and call appropriate
    function.
    Args:
        schema: str, @see docs #FIXME: add docs link

    Returns:
        nothing, just run appropriate ticks generator
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

    if schema.startswith('line'):
        schema_clr = schema.strip('line(').rstrip(')')
        try:
            rps_from, rps_to, duration = schema_clr.split(',')
        except ValueError, e:
            schema_format_err(schema)
        if not (rps_from.isdigit() and rps_to.isdigit() and\
                __validate_duration(duration)):
            schema_format_err(schema)

        duration = __trans_to_ms(duration)
        print 'line', rps_from, rps_to, duration
        rps_to = float(rps_to)
        rps_from = float(rps_from)

        for tick in line_shema(rps_from, rps_to, duration, tick_offset):
            yield tick

    elif schema.startswith('const'):
        schema_clr = schema.strip('const(').rstrip(')')
        try:
            rps, duration = schema_clr.split(',')
        except ValueError, e:
            schema_format_err(schema)
        if not (rps.isdigit() and __validate_duration(duration)):
            schema_format_err(schema)

        duration = __trans_to_ms(duration)
        for tick in const_shema(rps, duration, tick_offset):
            yield tick

    elif schema.startswith('step'):
        schema_clr = schema.strip('step(').rstrip(')')
        try:
            rps_from, rps_to, step_size, step_dur = schema_clr.split(',')
        except ValueError, e:
            schema_format_err(schema)

        if not (rps_from.isdigit() and rps_to.isdigit() and\
                step_size.isdigit() and __validate_duration(step_dur)):
            schema_format_err(schema)

        step_dur = __trans_to_ms(step_dur)
        rps_from = int(rps_from)
        rps_to = int(rps_to)
        step_size = int(step_size)

        # only positive step_size
        if (rps_from > rps_to) or (step_size <= 0):
            schema_format_err(schema)

        # TODO: negative step_size
        # check that chema isn't infinite
        #if (rps_from < rps_to and step_size <= 0) or\
        #        (rps_from > rps_to and step_size >= 0) or\
        #        step_size == 0:
        #    __schema_format_err(schema)

        for tick in step_shema(rps_from, rps_to, step_dur, step_size,
                tick_offset):
            yield tick
    else:
        schema_format_err(schema, msg=', Can\'t determine schema type')
