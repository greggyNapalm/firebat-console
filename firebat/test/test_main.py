import sys
sys.path.insert(0, '.')

import unittest
from firebat.console.conf import make_p_conf


class TestMain(unittest.TestCase):

    def test_smoke(self):
        self.assertEqual(1, 1)

