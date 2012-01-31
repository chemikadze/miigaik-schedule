# -:- coding: utf-8 -:-

from sources.datamodel import *
from sources.site import request_get, request_post, wrong_format, \
    parse_select_item, GroupDataContainer
from BeautifulSoup import BeautifulSoup

MIIGAIK_SCHEDULE_URL = 'http://studydep.miigaik.ru/semestr/index.php'

class SiteSource(DataSource):

    ROWCOUNT = 9
    WEEK_MAP = { u'верхняя': UPPER_WEEK, u'нижняя': LOWER_WEEK }
    WEEKDAYS = {
        u"Понедельник": 1,
        u"Вторник": 2,
        u"Среда": 3,
        u"Четверг": 4,
        u"Пятница": 5,
        u"Суббота": 6
    }

    def __init__(self):
        front_page_data = request_get(MIIGAIK_SCHEDULE_URL)
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

    def groups(self):
        return self._groups

    def group_data(self, group_id):
        # TODO: caching
        data = self.soup_for_group(group_id)
        table = self.choose_table(data)
        return self.parse_table(table)

    def table_is_valid(self, table):
        return len(table.findAll('th')) == self.ROWCOUNT and \
               table.tr and table.tr.th

    def choose_table(self, data):
        for table in data.findAll('table'):
            if self.table_is_valid(table):
                return table
        raise wrong_format(MIIGAIK_SCHEDULE_URL, 'can not find valid table')

    def row_to_lesson(self, cols):
        # TODO: remove HTML tags
        return Lesson(
            self.parse_week_day(cols[0].text.strip()),
            int(cols[1].text.split('-')[0]),
            cols[4].text,
            cols[5].text,
            cols[6].text,
            self.parse_week_type(cols[2].text.strip()),
            cols[3].text,
            cols[7].text
        )

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

    def parse_table(self, table):
        utemp = dict( (day, DaySchedule()) for day in xrange(1, 8) )
        ltemp = dict( (day, DaySchedule()) for day in xrange(1, 8) )
        for row in table.findAll('tr'):
            cells = row.findAll('td')
            if len(cells) == self.ROWCOUNT:
                try:
                    lesson = self.row_to_lesson(cells)
                except ValueError:
                    continue
                if lesson.week_type == UPPER_WEEK:
                    utemp[lesson.week_day].set_lesson(lesson.number, lesson)
                else:
                    ltemp[lesson.week_day].set_lesson(lesson.number, lesson)
        def conv(lst):
            p = lst.items()
            p.sort(lambda t1, t2: cmp(t1[0], t2[0]))
            return [ i for i in p if len(i[1])>0 ]
        return GroupDataContainer(conv(utemp), conv(ltemp))

    def post_params_for_group(self, group_id):
        return {
            "fak": group_id.faculty.encode('cp1251'),
            "kurs": group_id.year.encode('cp1251'),
            "grup": group_id.group.encode('cp1251'),
            "ok": u"Искать".encode('cp1251')
        }

    def soup_for_group(self, group_id):
        return BeautifulSoup(request_post(MIIGAIK_SCHEDULE_URL,
            parameters=self.post_params_for_group(group_id)))


DATA_SOURCE = SiteSource