# -:- coding: utf-8 -:-

from hashlib import sha1


class WeekType(object):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'Week("%s")' % self.name

    def __eq__(self, other):
        return self.name == other.name


UPPER_WEEK = WeekType("upper")
LOWER_WEEK = WeekType("lower")


WEEK_DAYS = (
    (u"Понедельник", 1),
    (u"Вторник", 2),
    (u"Среда", 3),
    (u"Четверг", 4),
    (u"Пятница", 5),
    (u"Суббота", 6)
)

MAP_DAY_STR = dict((id, s) for (s, id) in WEEK_DAYS)


class GroupId(object):

    """Identifier for group"""

    def __init__(self, faculty, year, group):
        self.faculty = faculty
        self.year = year
        self.group = group

    def __str__(self):
        return "GroupId(%s,%s,%s)" % (self.faculty, self.year, self.group)

    def uuid(self):
        return sha1(str(self)).hexdiget()


class DaySchedule(object):

    def __init__(self):
        self.__lessons = [None for x in xrange(16)]

    def set_lesson(self, number, lesson):
        self.__lessons[number] = lesson

    def lesson(self, number):
        return self.__lessons[number]

    def lessons(self):
        return self.__lessons

    def __len__(self):
        return len(self.__lessons)

    def list(self):
        return [lesson for lesson in self.__lessons if lesson]


class Lesson(object):

    def __init__(self, week_day, number, subject, tutor, auditory, week_type,
                 subdivision, type_):
        self.week_day = week_day       # int, from 1
        self.number = number           # int
        self.subject = subject         # string
        self.tutor = tutor             # string
        self.auditory = auditory       # string
        self.week_type = week_type     # WeekType
        self.subdivision = subdivision # string
        self.type = type_              # string


class DataSource(object):

    """Base class for some source of schedule data"""

    def group_data(self, group_id):
        raise NotImplementedError()

    def faculties(self):
        raise NotImplementedError()

    def years(self):
        raise NotImplementedError()

    def groups(self):
        raise NotImplementedError()


class GroupData(object):

    """Data for group (faculty+year+spec)"""

    def week(self, week_type):
        """Schedule for upper/lower week

        Returns list of tuples (weekday , DaySchedule)"""
        raise NotImplementedError()


class TimeTable(object):

    """Mapping between lessons and hours"""

    def start(self, number):
        raise NotImplementedError()

    def end(self, number):
        raise NotImplementedError()