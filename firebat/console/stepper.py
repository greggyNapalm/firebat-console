# -*- coding: utf-8 -*-

"""
firebat.stepper
~~~~~~~~~~~~~~~

Generate stepped ammo(input data + load schema)
"""

import os
import string

from exceptions import StepperAmmoFormat, StepperSchemaFormat


def schema_format_err(schema, msg=None):
    ''' Compile exception data in obj attr and rise it.
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


def validate_duration(duration):
    '''Check conformity of short notation
    Args:
        duration: str with declare time interval in short notation

    Returns:
        bool, true if short notation is valid
    '''
    trans_table = string.maketrans('', '')
    allowed = string.digits + 'mh'
    return not duration.translate(trans_table, allowed)


def trans_to_ms(duration, schema,):
    '''Transfer duration from short notation to milliseconds
    Args:
        duration: str with declare time interval in short notation
        schema: list, used in exception to be able to display in UI.

    Returns:
        int, time interval in milliseconds
    '''
    if not validate_duration(duration):
        schema_format_err(schema, msg=', Duration malformed')
    if duration.endswith('m'):
        duration = int(duration.rstrip('m')) * 60
    elif duration.endswith('h'):
        duration = int(duration.rstrip('h')) * 60 ** 2
    else:
        duration = int(duration)
    return duration * 10 ** 3


def parse_schema(schema):
    ''' Parse and validate load algorithm(load schema).
    Args:
        schema: list, @see docs # TODO: add docs link.

    Returns:
        dict with translated data (All in milliseconds).
    '''
    if not isinstance(schema, list):
        schema_format_err(schema, msg=', Schema shud be list')
    if schema[0] == 'const':
        rps, duration_s = schema[-2:]
        # from simplejson 2.0.1 we have unicode instead bytestr
        if isinstance(duration_s, unicode):
            duration_s = duration_s.encode('utf-8')
        elif not isinstance(duration_s, basestring):
            schema_format_err(schema)

        if not isinstance(rps, int):
            schema_format_err(schema)

        result = {
            'format': 'const',
            'rpms': rps / 1000.0,
            'duration': trans_to_ms(duration_s, schema),
        }
        return result
    elif schema[0] == 'step':
        rps_from, rps_to, step_size, step_dur = schema[-4:]
        if not (isinstance(rps_from, int) and\
                isinstance(rps_to, int) and\
                isinstance(step_size, int)):
            schema_format_err(schema)

        # from simplejson 2.0.1 we have unicode instead bytestr
        if isinstance(step_dur, unicode):
            step_dur = step_dur.encode('utf-8')
        elif not isinstance(step_dur, basestring):
            schema_format_err(schema)

        if (rps_from > rps_to) or (step_size <= 0):
            schema_format_err(schema, msg=', only growing load allowed')

        step_dur = trans_to_ms(step_dur, schema)
        steps_num = (rps_to - rps_from) / step_size
        duration = (steps_num + 1) * step_dur
        result = {
            'format': 'step',
            'rpms_from': rps_from / 1000.0,
            'rpms_to': rps_to / 1000.0,
            'step_size': step_size / 1000.0,
            'step_dur': step_dur,
            'duration': duration,
        }
        return result
    elif schema[0] == 'line':
        rps_from, rps_to, duration = schema[-3:]
        if not (isinstance(rps_from, int) and\
                isinstance(rps_to, int)): 
            schema_format_err(schema)

        # from simplejson 2.0.1 we have unicode instead bytestr
        if isinstance(duration, unicode):
            duration_s = duration.encode('utf-8')
        elif not isinstance(duration, basestring):
            schema_format_err(schema)

        if (rps_from > rps_to):
            schema_format_err(schema, msg=', only growing load allowed')

        if isinstance(duration,  unicode):
            duration = duration.encode('utf-8')
        result = {
            'format': 'line',
            'rpms_from': rps_from / 1000.0,
            'rpms_to': rps_to / 1000.0,
            'duration': trans_to_ms(duration, schema),
        }
        return result
    else:
        schema_format_err(schema, msg=', Can\'t determine schema type')


def parse_ammo(ammo_fh):
    '''Validate and reformat input requests data(ammo file)
    Args:
        ammo_fh: File object, content in lunapark ammo format

    Returns:
        generator, which yield tuple with metaline and request text
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
        yield (line_form, chunk)


def const_shema(rpms, duration, tick_offset):
    '''Make time ticks from constraint load algorithm(load schema)
    Args:
        rpms: int,request peer millisecond
        duration: load chank duration in milliseconds
        tick_offset: int, first tick offset in milliseconds

    Returns:
        generator obj, which yields int time tick in milliseconds
    '''
    surplus = 0.0
    for t in xrange(tick_offset, tick_offset + duration + 1):
        surplus += rpms
        ticks_in_ms = round(surplus)
        for indx in xrange(int(ticks_in_ms)):
            yield t
        surplus -= ticks_in_ms


def step_shema(rpms_from, rpms_to, step_dur, step_size, tick_offset):
    '''Make time ticks from step load algorithm(load schema)
    Args:
        rpms_from: int, first step load(request peer millisecond)
        rpms_to: int, last step load(request peer millisecond)
        step_dur: int, each step time length in milliseconds
        step_size: int, rpms difference between two neighboring steps
        tick_offset: int, previous time tick position

    Returns:
        generator obj, which yields int time tick in milliseconds
    '''
    cur_step = rpms_from
    cur_step_border = tick_offset
    while cur_step <= rpms_to:
        cntr = 0.0
        for tick in const_shema(cur_step, step_dur, cur_step_border):
            cntr += 1
            yield tick
        cur_step += step_size
        cur_step_border += step_dur


def line_shema(rpms_from, rpms_to, duration, tick_offset):
    '''Make time ticks from line load algorithm(load schema)
    Args:
        rpms_from: int, starting load
        rpms_to: int, ending load
        duration: int, time length in milliseconds
        tick_offset: int, previous time tick position

    Returns:
        generator obj, which yields int time tick in milliseconds
    '''
    der = (rpms_to - rpms_from) / duration  # load derivative
    ticks_in_ms = rpms_from
    proficit = 1.0
    up = 0.0  # inaccuracy, because request in millisecond is int, func linear

    for t in xrange(tick_offset, tick_offset + duration + 1):
        if ticks_in_ms > 1:
            for indx in xrange(int(ticks_in_ms)):
                yield t
        else:
            proficit += ticks_in_ms
            if proficit > 1.0:
                yield t
                proficit -= 1.0
        load = rpms_from + der * t

        up = up + load - ticks_in_ms
        deficit = up - 1.0
        if deficit > 0:
            yield t
            up = deficit

        if int(load - ticks_in_ms) >= 1:
            ticks_in_ms = int(load)


def process_load_schema(schema, tick_offset):
    ''' Parse and validate load algorithm(load schema) and call appropriate
    function.
    Args:
        schema: list, @see docs #FIXME: add docs link
        tick_offset: int, previous time tick position

    Returns:
        runs appropriate ticks generator, which yields time ticks(int).
    '''
    s = parse_schema(schema)
    if s['format'] == 'const':
        gen = const_shema(s['rpms'], s['duration'], tick_offset)
    elif s['format'] == 'step':
        gen = step_shema(s['rpms_from'], s['rpms_to'], s['step_dur'],\
                         s['step_size'], tick_offset)
    elif s['format'] == 'line':
        gen = line_shema(s['rpms_from'], s['rpms_to'], s['duration'],\
                         tick_offset)
    else:
        schema_format_err(schema, msg=', schema pasrser malformed!')
    for tick in gen:
        yield tick


def const_series(rps, duration, tick_offset):
    '''Make data series in Highcharts format from constraint load schema.
    Args:
        rps: int,request peer second
        duration: load chank duration in seconds
        tick_offset: int, first tick offset in seconds(epoch)

    Returns:
        series: list of tuples, Highcharts data series.
    '''
    result = []
    surplus = 0.0
    for t in xrange(tick_offset, tick_offset + duration + 1):
        surplus += rps
        ticks_in_s = round(surplus)
        result.append((t, int(ticks_in_s)))
        surplus -= ticks_in_s
    return result


def step_series(rps_from, rps_to, step_dur, step_size, tick_offset):
    '''Make data series in Highcharts format from step load schema.
    Args:
        rps_from: int, first step load(request peer second)
        rps_to: int, last step load(request peer second)
        step_dur: int, each step time length in seconds
        step_size: int, rps difference between two neighboring steps
        tick_offset: int, previous time tick position

    Returns:
        series: list of tuples, Highcharts data series.
    '''
    result = []
    cur_step = rps_from
    cur_step_border = tick_offset
    while cur_step <= rps_to:
        result.extend(const_series(cur_step, step_dur, cur_step_border))
        cur_step += step_size
        cur_step_border += step_dur
    return result


def line_series(rps_from, rps_to, duration, tick_offset):
    '''Make time ticks from line load algorithm(load schema)
    Args:
        rps_from: int, starting load
        rps_to: int, ending load
        duration: int, time length in seconds
        tick_offset: int, previous time tick position

    Returns:
        series: list of tuples, Highcharts data series.
    '''
    result = []
    der = (rps_to - rps_from) / duration  # load derivative
    proficit = 0

    for t in xrange(tick_offset, tick_offset + duration + 1):
        t_num = t - tick_offset  # second number
        load = rps_from + der * t_num
        proficit += load
        if proficit >= 1:
            rps_drop = int(proficit)
            # no need to convert epoach to JS time stamps,
            # that will be done earlier on client side(JS).
            result.append((t, rps_drop))
            proficit -= rps_drop
        else:
            result.append((t, 0))

    return result


def series_from_schema(schema, tick_offset):
    ''' Parse and validate load algorithm(load schema) and call appropriate
    function.
    Args:
        schema: list, @see docs #FIXME: add docs link
        tick_offset: int, previous time tick position(epoch)

    Returns:
        series: list of tuples, Highcharts data series.
    '''
    s = parse_schema(schema)
    if s['format'] == 'const':
        return const_series(s['rpms'] * 1000, s['duration'] / 1000,
                            tick_offset)
    elif s['format'] == 'step':
        return step_series(s['rpms_from'] * 1000, s['rpms_to'] * 1000,\
                s['step_dur'] / 1000, s['step_size'] * 1000, tick_offset)
    elif s['format'] == 'line':
        return line_series(s['rpms_from'] * 1000, s['rpms_to'] * 1000,\
                s['duration'] / 1000, tick_offset)
    else:
        schema_format_err(schema, msg=', schema pasrser malformed!')


def fire_duration(fire):
    ''' Calculate total fire(job) duration.
    Args:
        fire: dict from cfg file.

    Returns:
        int, duration in milliseconds.
    '''
    total_duration = 0
    for schema in fire['load']:
        total_duration += parse_schema(schema)['duration']
    return total_duration
