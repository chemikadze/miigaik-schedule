# -:- coding: utf-8 -:-

from sources.versions import site_12_03_2013
from sources.util import empty_data
import logging


class SiteSource(site_12_03_2013.SiteSource):

    def table_is_valid(self, table):
        return len(table.findAll('th')) == self.ROWCOUNT and \
               table.find('tr', recursive=False) and \
               table.find('tr', recursive=False).find('th', recursive=False)


DATA_SOURCE = SiteSource
TIMETABLE = site_12_03_2013.TIMETABLE