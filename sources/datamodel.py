from hashlib import sha1


class WeekType(object):

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return 'Week("%s")' % self.name


UPPER_WEEK = WeekType("upper")
LOWER_WEEK = WeekType("lower")


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


class Lesson(object):

    def __init__(self, week_day, number, subject, tutor, auditory, week_type,
                 subdivision, type_):
        self.week_day = week_day
        self.number = number
        self.subject = subject
        self.tutor = tutor
        self.auditory = auditory
        self.week_type = week_type
        self.subdivision = subdivision
        self.type = type_


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