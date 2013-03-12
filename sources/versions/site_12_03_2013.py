# -:- coding: utf-8 -:-

from logging import getLogger
import HTMLParser

from BeautifulSoup import BeautifulSoup

from sources.versions import site_21_12_2012
from sources.datamodel import GroupId
from sources.site import wrong_format, parse_select_item
from sources.util import uniq


logger = getLogger()
_parser = HTMLParser.HTMLParser()


def _un(string):
    return _parser.unescape(string).replace('&nbsp;', ' ')


MIIGAIK_SCHEDULE_URL = 'http://studydep.miigaik.ru/semestr/index.php'


class SiteSource(site_21_12_2012.SiteSource):

    def __init__(self):
        def find_form(dom):
            forms = dom.findAll('form')
            if len(forms) > 1:
                wrong_format(MIIGAIK_SCHEDULE_URL, 'more than one form')
            return forms[0]

        def pull_out_list(form, name):
            return [i for i in parse_select_item(
                form.find('select',
                          attrs={u"name": name}))
                    if i["text"].strip() and i["value"]]
        front_page_data = self.request_get(MIIGAIK_SCHEDULE_URL)
        faculties = pull_out_list(
            find_form(BeautifulSoup(front_page_data)), 'fak')
        years = list()
        groups = list()
        for faculty in faculties:
            dom = self.soup_for_group(GroupId(faculty['value'], u'', u''))
            new_years = pull_out_list(find_form(dom), 'kurs')
            logger.info("Got years: %s" % new_years)
            years.extend(new_years)
            for year in new_years:
                gdom = self.soup_for_group(
                    GroupId(faculty['value'], year['value'], u''))
                new_groups = pull_out_list(find_form(gdom), 'grup')
                groups.extend(new_groups)
        self._faculties = sorted(faculties)
        self._years = sorted(uniq(years))
        self._groups = sorted(uniq(groups))


DATA_SOURCE = SiteSource
TIMETABLE = site_21_12_2012.HardcodedTimetable
