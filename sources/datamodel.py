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


class ClassroomId(object):

    """Identifier for classroom"""

    def __init__(self, building, number):
        self.building = building
        self.number = number

    def __str__(self):
        return "ClassroomId(%s,%s)" % (self.building, self.number)
    __repr__ = __str__

    def __hash__(self):
        return hash(self.building) + hash(self.number)

    def __cmp__(self, other):
        return cmp(self.building, other.building) or \
               cmp(self.number, other.number)


class GroupId(object):

    """Identifier for group"""

    def __init__(self, faculty, year, group):
        """Faculty, year and group are 'value' params"""
        self.faculty = faculty
        self.year = year
        self.group = group

    def __hash__(self):
        return hash(self.faculty) + hash(self.year) + hash(self.group)

    def __cmp__(self, other):
        return cmp(self.faculty, other.faculty) or cmp(self.year, other.year)\
                or cmp(self.group, other.group)

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

    def __init__(self, group_id, week_day, number, subject, tutor, auditory, week_type,
                 subdivision, type_, classroom_id):
        self.group_id = group_id       # GroupId
        self.week_day = week_day       # int, from 1
        self.number = number           # int
        self.subject = subject         # string
        self.tutor = tutor             # string
        self.auditory = auditory       # string
        self.classroom_id = classroom_id # ClassroomId
        self.week_type = week_type     # WeekType
        self.subdivision = subdivision # string
        self.type_ = type_             # string


class DataSource(object):

    """Base class for some source of schedule data"""

    def group_data(self, group_id):
        raise NotImplementedError()

    def classroom_data(self, classroom_id):
        raise NotImplementedError()

    def faculties(self):
        raise NotImplementedError()

    def years(self):
        raise NotImplementedError()

    def groups(self, faculty_id=None, year=None):
        raise NotImplementedError()

    def groups_data(self, faculty_id=None):
        raise NotImplementedError()

    def classrooms(self):
        """Returns list of names of ClassroomIds"""
        raise NotImplementedError()

    def buildings(self):
        """Returns list of building names"""
        raise NotImplementedError()

    def free_classrooms(self, week, day, lessons, building):
        """Returns list of ClassromId's"""
        raise NotImplementedError()

    def valid_comp(self, year, group):
        raise NotImplementedError()


class GroupData(object):

    """Data for group (faculty+year+spec)"""

    def group_id(self):
        raise NotImplementedError()

    def week(self, week_type):
        """Schedule for upper/lower week

        Returns list of tuples (weekday , DaySchedule)"""
        raise NotImplementedError()


class ClassroomData(object):

    """Data for classroom"""

    def classroom_id(self):
        raise NotImplementedError()

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

    def lesson(self, time):
        raise NotImplementedError()
