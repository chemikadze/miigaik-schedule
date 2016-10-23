import os
import sys
import unittest
from datetime import date

ROOT_PATH = os.path.dirname(os.path.dirname(__file__))
sys.path.append(ROOT_PATH)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'gaenv'))

from rasp_vuzov_api import api_v2


class WeeksTest(unittest.TestCase):

    def test_rasp_weeks(self):
        def verify(input_date, expected):
            was = api_v2._rasp_vuzov_week_number(input_date)
            self.assertEquals(
                was,
                expected,
                "Failed on date %s: was %s, expected %s" % (input_date, was, expected))
        verify(date(2014, 01, 01), 1)
        verify(date(2014, 01, 06), 2)
        verify(date(2015, 01, 01), 1)
        verify(date(2015, 01, 05), 2)
        verify(date(2016, 01, 01), 1)
        verify(date(2016, 01, 04), 2)
