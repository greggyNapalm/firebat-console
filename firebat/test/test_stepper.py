import sys
sys.path.insert(0, '.')
import unittest

from firebat.console.stepper import parse_ammo, process_load_schema
from firebat.console.stepper import fire_duration, trans_to_ms
from firebat.console.stepper import validate_duration
from firebat.console.exceptions import StepperAmmoFormat, StepperSchemaFormat

from base import get_fire_dict


class TestMain(unittest.TestCase):

    def test_duration_calc(self):
        f = get_fire_dict()
        f['load'] = [
            ['line', 1, 10, '2m'],
            ['step', 100, 150, 5, '1m'],
        ]
        # line duration 2m = 2 * 60 * 1000 = 120000 ms
        # steps duration ((150 - 100) / 5 + 1) * 1 * 60 * 1000 = 660000 ms
        self.assertEqual(fire_duration(f), 120000 + 660000)

    def test_validate_duration(self):
        # only two letters allowed in short notation
        # 'm' - minutes; 'h' - hours
        self.assertTrue(validate_duration('123'))
        self.assertTrue(validate_duration('123m'))
        self.assertTrue(validate_duration('123h'))
        self.assertFalse(validate_duration('123 light years'))


    def test_trans_to_ms(self):
        # trying to translate malformed duration
        with self.assertRaises(StepperSchemaFormat):
            trans_to_ms('123 light years', [])

        self.assertEqual(trans_to_ms('2m', []), 120000)
        self.assertEqual(trans_to_ms('10h', []), 36000000)
