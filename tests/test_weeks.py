import unittest

from sources.datamodel import UPPER_WEEK, LOWER_WEEK
from sources import util


class WeeksTest(unittest.TestSuite):

    def test_weektype_to_number(self):
        assert util._week_type_to_number(UPPER_WEEK) == 1
        assert util._week_type_to_number(LOWER_WEEK) == 2
