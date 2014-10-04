# -:- coding: utf-8 -:-

import calendar
from datetime import timedelta, tzinfo, datetime
import re
from time import sleep
from datamodel import UPPER_WEEK, LOWER_WEEK
import logging
import sources
from sources.datamodel import DaySchedule

import os
import sys
ROOT_PATH = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(ROOT_PATH, 'icalendar/src/'))
from icalendar import Calendar, Event, vCalAddress, vRecur, vDatetime


class FixedOffset(tzinfo):

    def __init__(self, offset, name):
        self.__offset = timedelta(minutes=offset)
        self.__name = name

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return timedelta()


MOSCOW_TZ = FixedOffset(4 * 60, 'Europe/Moscow')


def merged_days(first, second):
    result = []
    for f, s in zip(first.lessons(), second.lessons()):
        if f:
            result.append(f)
        if s:
            result.append(s)
    return result


def merged_weeks(upper, lower):
    upper = dict(upper)
    lower = dict(lower)
    result = \
        [merged_days(upper.get(i, DaySchedule()), lower.get(i, DaySchedule()))
         for i in xrange(7)]
    return [x for x in result if x]


def locate(seq, pred, default=None):
    for item in seq:
        if pred(item):
            return item
    return default


def get_week_type(date):
    weeknum = int(date.strftime('%W'))
    return (weeknum % 2) and UPPER_WEEK or LOWER_WEEK


def current_week():
    # I don't want dateutil or pytz in source tree, really
    return get_week_type(datetime.now(MOSCOW_TZ))


def current_weekday():
    now = datetime.now(MOSCOW_TZ)
    weeknum = int(now.strftime('%w'))
    return weeknum


def current_lesson():
    now = datetime.now(MOSCOW_TZ)
    return sources.versions.CURRENT_TIMETABLE().lesson(now.timetz())


def group_data_to_ical(group_data, timetable, pred=None):
    cal = Calendar()

    cal.add('version', '2.0')
    cal.add('prodid', '-//chemikadze/miigaik-schedule-ng/ical')
    cal.add('method', 'PUBLISH')

    for week_type in (LOWER_WEEK, UPPER_WEEK):
        week = group_data.week(week_type)

        now = datetime.now(MOSCOW_TZ)
        oneday = timedelta(days=1)
        start_date = now.date()
        while start_date.weekday() != calendar.MONDAY:
            start_date -= oneday
        while get_week_type(start_date) != week_type:
            start_date -= oneday * 7

        for day_id, day in week:
            for lesson in day.lessons():
                if lesson and (not pred or pred(lesson)):
                    lesson_date = start_date + oneday * (lesson.week_day - 1)
                    event = \
                        lesson_as_ical_event(lesson, lesson_date, timetable)
                    cal.add_component(event)
    return cal


def lesson_as_ical_event(lesson, lesson_date, timetable):
    event = Event()
    event.add('uuid', lesson_uuid(lesson))
    event.add('summary', lesson.subject)
    addr = vCalAddress('MAILTO:none@miigaik.ru')
    addr.params['CN'] = lesson.tutor.encode('utf-8')
    event['organizer'] = addr
    event.add('location', lesson.auditory)
    event.add('rrule', vRecur({'freq': 'WEEKLY', 'interval': 2}))

    start_time = timetable.start(lesson.number)
    end_time = timetable.end(lesson.number)

    event['dtstart'] = vDatetime(
        datetime(lesson_date.year, lesson_date.month,
                 lesson_date.day, start_time.hour, start_time.minute,
                 tzinfo=start_time.tzinfo))
    event['dtend'] = vDatetime(
        datetime(lesson_date.year, lesson_date.month,
                 lesson_date.day, end_time.hour, end_time.minute,
                 tzinfo=end_time.tzinfo))

    return event


def lesson_uuid(lesson):
    data = lesson.__dict__
    return u'%(week_type)s-%(week_day)s-%(number)s/' + \
        '%(subject)s-%(tutor)s-%(type_)s@miigaik-schedule-ng' % data


class AutoaddDict(dict):

    def __init__(self, proto_gen):
        super(AutoaddDict, self).__init__()
        self.proto_gen = proto_gen

    def __getitem__(self, id):
        try:
            return super(AutoaddDict, self).__getitem__(id)
        except KeyError:
            elem = self.proto_gen(id)
            super(AutoaddDict, self).__setitem__(id, elem)
            return elem


def empty_data(data):
    return not any(any(dv[1].list() for dv in data.week(w))
                   for w in (UPPER_WEEK, LOWER_WEEK))


def force_str(v):
    if isinstance(v, basestring):
        return v
    else:
        return str(v)


def with_retry(f):
    def wrapper(*args, **kwargs):
        retry = kwargs.pop('retry', 5)
        for i in xrange(1, retry + 1):
            if i != retry:
                try:
                    return f(*args, **kwargs)
                except Exception as e:
                    logging.warning("Exception catched in retry block: %s", e)
                    sleep(10 * (i + 1))
                    pass
            else:
                return f(*args, **kwargs)
    return wrapper


def human_cmp(a, b):
    # thnx to Jeff Atwood (codinghorror.com)
    convert = lambda text: int(text) if text.isdigit() else text
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return cmp(alphanum_key(a), alphanum_key(b))


def cid_cmp(a, b):
    res = human_cmp(a.building, b.building)
    if not res:
        return human_cmp(a.number, b.number)
    else:
        return res


def uniq(list_):
    new = []
    for i in list_:
        if i not in new:
            new.append(i)
    return new
