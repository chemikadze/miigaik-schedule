# -:- coding: utf-8 -:-

from logging import getLogger
import HTMLParser

from BeautifulSoup import BeautifulSoup

from sources.versions import site_21_12_2012
from sources.datamodel import GroupId, Lesson
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
        group_ids = list()
        for faculty in faculties:
            dom = self.soup_for_group(GroupId(faculty['value'], u'', u''))
            new_years = pull_out_list(find_form(dom), 'kurs')
            years.extend(new_years)
            for year in new_years:
                gdom = self.soup_for_group(
                    GroupId(faculty['value'], year['value'], u''))
                new_groups = pull_out_list(find_form(gdom), 'grup')
                groups.extend(new_groups)
                for new_group in new_groups:
                    new_id = GroupId(
                        faculty['value'], year['value'], new_group['value'])
                    group_ids.append((new_id, new_group['text']))
        self._faculties = sorted(faculties)
        self._years = sorted(uniq(years))
        self._groups = sorted(uniq(groups))
        self._group_ids = group_ids

    def group_ids(self):
        return self._group_ids

    def row_to_lesson(self, group_id, cols):
        # TODO: remove HTML tags
        return Lesson(
            group_id,
            self.parse_week_day(_un(cols[0].text).strip()),
            int(_un(cols[1].text).split('-')[0]),
            _un(cols[4].text),
            _un(cols[5].getText(u", ")),
            _un(cols[6].text),
            self.parse_week_type(_un(cols[2].text).strip()),
            _un(cols[3].text),
            _un(cols[7].text),
            self.classroom_id_from_string(_un(cols[6].text))
        )


DATA_SOURCE = SiteSource
TIMETABLE = site_21_12_2012.HardcodedTimetable
