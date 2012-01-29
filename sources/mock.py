from datamodel import *
from site import GroupDataContainer

class MockDataSource(DataSource):

    def faculties(self):
        return [x for x in ['FoAC', 'FoAF']]

    def years(self):
        return map(str, xrange(1, 5))

    def groups(self):
        return [ '%s_%s' % (fac, yr)
                    for fac in self.faculties()
                       for yr in self.years()]

    def group_data(self, group_id):
        lower = self.__less_for_params(group_id.faculty, group_id.year,
            group_id.group, LOWER_WEEK)
        upper = self.__less_for_params(group_id.faculty, group_id.year,
            group_id.group, UPPER_WEEK)
        return GroupDataContainer(upper, lower)


    def __less_for_params(self, f, y, g, w):
        return [
            (day, self.__day(f, y, g, w, day))
            for day in xrange(1, 6-int(y)+1)
        ]

    def __day(self, f, y, g, w, d):
        lst = [
            Lesson(
                d, i,
                ("%s's_pain_%s_for_%s_%s") % (f, d, g, w),
                "Old %s's tutor" % f,
                1488+int(y)*10+d,
                w, 'subXXX', 'practice')
            for i in xrange(1, d+1)
        ]
        sched = DaySchedule()
        for lesson in lst:
            sched.set_lesson(lesson.number, lesson)
        return sched
