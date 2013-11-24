# -*- coding: UTF-8 -*-

from datamodel import *
from site import GroupDataContainer

class MockDataSource(DataSource):

    def __init__(self):
        def itemize(x):
            return {'text': x, 'value': x}
        self._faculties = [itemize(x) for x in [u'АФ', u'ГФ']]
        self._years =[itemize(x) for x in map(str, xrange(1, 2))]
        self._groups = [itemize('%s_%s' % (fac['value'], yr['value']))
                          for fac in self.faculties()
                            for yr in self.years()]

    def faculties(self):
        return self._faculties

    def years(self):
        return self._years

    def groups(self):
        return self._groups

    def __externalize(self, list):
        return [x['value'] for x in list]

    def group_data(self, group_id):
        lower = self.__week_for_params(group_id, group_id.faculty, group_id.year,
            group_id.group, LOWER_WEEK)
        upper = self.__week_for_params(group_id, group_id.faculty, group_id.year,
            group_id.group, UPPER_WEEK)
        return GroupDataContainer(group_id, upper, lower)

    @classmethod
    def valid_comp(self, year, group):
        return True

    def __week_for_params(self, id, f, y, g, w):
        return [
            (day, self.__day(id, f, y, g, w, day))
            for day in xrange(w == UPPER_WEEK and 1 or 0, 6-int(y)+1, 2)
        ]

    def __day(self, id, f, y, g, w, d):
        lst = [
            Lesson(
                id, d, i,
                (u"%s's_pain_%s_for_%s_%s") % (f, d, g, w.name),
                u"Старый %s's tutor" % f,
                u"%sк%s" % (str(1488+int(y)*10+d), d),
                w, u'subXXX', u'лекция',
                ClassroomId(str(d), str(1488+int(y)*10+d)))
            for i in xrange(1, d+1)
        ]
        sched = DaySchedule()
        for lesson in lst:
            sched.set_lesson(lesson.number, lesson)
        return sched
