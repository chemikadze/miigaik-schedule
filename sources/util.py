import calendar
from datetime import timedelta, tzinfo, datetime
from datamodel import UPPER_WEEK, LOWER_WEEK
from sources.datamodel import DaySchedule
from time import localtime, strftime, gmtime

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
    result = [merged_days(upper.get(i, DaySchedule()),
                lower.get(i, DaySchedule()))
                for i in xrange(7)]
    return [x for x in result if x]


def locate(seq, pred, default=None):
    for item in seq:
        if pred(item):
            return item
    return default


class FixedOffset(tzinfo):

    def __init__(self, offset, name):
        self.__offset = timedelta(minutes = offset)
        self.__name = name

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return timedelta()


def current_week():
    # I don't want dateutil or pytz in source tree, really
    now = datetime.now(FixedOffset(4*60, 'Europe/Moscow'))
    weeknum = int(now.strftime('%W'))
    return (weeknum % 2) and LOWER_WEEK or UPPER_WEEK