# -:- coding: utf-8 -:-

from datetime import time
import re

from sources.datamodel import DataSource, UPPER_WEEK, LOWER_WEEK, \
    Lesson, DaySchedule, ClassroomId, TimeTable
from sources.site import request_get, request_post, wrong_format, \
    parse_select_item, GroupDataContainer
from BeautifulSoup import BeautifulSoup
from sources.util import MOSCOW_TZ, with_retry

import HTMLParser

_parser = HTMLParser.HTMLParser()


def _un(string):
    return _parser.unescape(string).replace('&nbsp;', ' ')


MIIGAIK_SCHEDULE_URL = 'http://studydep.miigaik.ru/semestr/index.php'


class SiteSource(DataSource):

    ROWCOUNT = 9
    WEEK_MAP = {u'верхняя': UPPER_WEEK, u'нижняя': LOWER_WEEK}
    WEEKDAYS = {
        u"Понедельник": 1,
        u"Вторник": 2,
        u"Среда": 3,
        u"Четверг": 4,
        u"Пятница": 5,
        u"Суббота": 6
    }

    def __init__(self):
        front_page_data = self.request_get(MIIGAIK_SCHEDULE_URL)
        dom = BeautifulSoup(front_page_data)
        forms = dom.findAll('form')
        if len(forms) > 1:
            wrong_format(MIIGAIK_SCHEDULE_URL, 'more than one form')
        form = forms[0]

        def pull_out_list(name):
            return [i for i in parse_select_item(form.find('select',
                                                 attrs={u"name": name}))

                    if i["text"].strip() and i["value"]]
        self._faculties = pull_out_list('fak')
        self._years = pull_out_list('kurs')
        self._groups = pull_out_list('grup')

    def __externalize(self, list):
        return [x['value'] for x in list]

    def faculties(self):
        return self._faculties

    def years(self):
        return self._years

    def groups(self, faculty_id=None, year=None):
        if faculty_id or year:
            raise Exception("Filtering by year and faculty is not supported.")
        return self._groups

    def group_data(self, group_id):
        # TODO: caching
        data = self.soup_for_group(group_id)
        table = self.choose_table(data)
        return self.parse_table(group_id, table)

    def table_is_valid(self, table):
        return len(table.findAll('th')) == self.ROWCOUNT and \
            table.tr and table.tr.th

    def choose_table(self, data):
        for table in data.findAll('table'):
            if self.table_is_valid(table):
                return table
        raise wrong_format(MIIGAIK_SCHEDULE_URL, 'can not find valid table')

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

    @with_retry
    def request_get(self, *args, **kwargs):
        return request_get(*args, **kwargs)

    @with_retry
    def request_post(self, *args, **kwargs):
        return request_post(*args, **kwargs)

    def parse_week_type(self, text):
        try:
            return self.WEEK_MAP[text]
        except KeyError:
            wrong_format(MIIGAIK_SCHEDULE_URL, 'can not parse week type')

    def parse_week_day(self, text):
        try:
            for (k, n) in self.WEEKDAYS.items():
                if k in text:
                    return n
        except KeyError:
            wrong_format(MIIGAIK_SCHEDULE_URL, 'can not parse weekday')

    def parse_table(self, group_id, table):
        utemp = dict((day, DaySchedule()) for day in xrange(1, 8))
        ltemp = dict((day, DaySchedule()) for day in xrange(1, 8))
        for row in table.findAll('tr'):
            cells = row.findAll('td')
            if len(cells) == self.ROWCOUNT and\
                    any(_un(t.text).strip() for t in cells):
                try:
                    lesson = self.row_to_lesson(group_id, cells)
                except ValueError as e:
                    wrong_format(MIIGAIK_SCHEDULE_URL,
                                 'can not parse lesson because of %s' % e)
                if lesson.week_type == UPPER_WEEK:
                    utemp[lesson.week_day].set_lesson(lesson.number, lesson)
                else:
                    ltemp[lesson.week_day].set_lesson(lesson.number, lesson)

        def conv(lst):
            p = lst.items()
            p.sort(lambda t1, t2: cmp(t1[0], t2[0]))
            return [i for i in p if len(i[1]) > 0]

        return GroupDataContainer(group_id, conv(utemp), conv(ltemp))

    def post_params_for_group(self, group_id):
        return {
            "fak": group_id.faculty.encode('cp1251'),
            "kurs": group_id.year.encode('cp1251'),
            "grup": group_id.group.encode('cp1251'),
            "ok": u"Искать".encode('cp1251')
        }

    def soup_for_group(self, group_id):
        return BeautifulSoup(self.request_post(MIIGAIK_SCHEDULE_URL,
                             parameters=self.post_params_for_group(group_id)))

    @classmethod
    def valid_comp(cls, year, group):
        nums = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6}
        try:
            return int(year['text']) == \
                nums.get(group['text'].split(' ')[1].split('-')[0], 0)
        except ValueError:
            return False

    @staticmethod
    def classroom_id_from_string(txt):
        if u'воен.' in txt:
            return ClassroomId('1', txt.strip())
        elif u'шк.' == txt[:3]:
            return ClassroomId(u'шк', txt[3:].strip())
        elif u'шк' == txt[:2]:
            return ClassroomId(u'шк', txt[2:].strip())
        m = re.match(ur"(\d+)(\s*к.?\s*(\d+))?", txt.strip())
        if m:
            aud, building = m.group(1), m.group(3)
        else:
            aud = txt.strip()
            building = None
        if not building:
            building = u'1'
        return ClassroomId(building, aud)


def _tm(hour, minute):
    return time(hour, minute, tzinfo=MOSCOW_TZ)


class HardcodedTimetable(TimeTable):

    data = {
        1: [_tm(9, 00), _tm(10, 30)],
        2: [_tm(10, 40), _tm(12, 10)],
        3: [_tm(12, 50), _tm(14, 20)],
        4: [_tm(14, 30), _tm(16, 00)],
        5: [_tm(16, 10), _tm(17, 40)],
        6: [_tm(17, 50), _tm(19, 20)],
        7: [_tm(19, 30), _tm(21, 00)]
    }
    sdata = sorted(data.items(), cmp=lambda x, y: cmp(x[0], y[0]))

    def start(self, number):
        return self.data[number][0]

    def end(self, number):
        return self.data[number][1]

    def lesson(self, time):
        for (i, bounds) in self.sdata:
            if bounds[0] <= time <= bounds[1]:
                return i
            if time < bounds[0]:
                return i
        return None


DATA_SOURCE = SiteSource
TIMETABLE = HardcodedTimetable
