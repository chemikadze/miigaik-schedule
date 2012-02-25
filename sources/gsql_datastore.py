from datetime import datetime
import json
from google.appengine.ext import db
from sources.datamodel import Lesson, LOWER_WEEK, UPPER_WEEK, DaySchedule, GroupData, GroupId, ClassroomId, ClassroomData, DataSource
from sources.site import GroupDataContainer, ClassroomDataContainer
import logging
from sources.util import AutoaddDict


class NoVersionStoredException(Exception):
    pass


class GsqlVersion(db.Model):

    version = db.IntegerProperty()
    create_time = db.DateTimeProperty()

    valid = db.BooleanProperty()


class GsqlStoreConfiguration(db.Model):

    current_version = db.IntegerProperty()


class GsqlGroupLesson(db.Model):

    version = db.IntegerProperty()
    update_time = db.DateTimeProperty()

    # contains only "value" from id dictionary
    faculty = db.StringProperty()
    year = db.StringProperty() # string for compatibility
    group = db.StringProperty()

    week_day = db.IntegerProperty()
    number = db.IntegerProperty()
    subject = db.StringProperty()
    tutor = db.StringProperty()
    auditory = db.StringProperty()
    week_type = db.StringProperty()
    subdivision = db.StringProperty()
    type_ = db.StringProperty()

    IDENTITY_FIELDS = {
        'week_day': int,
        'number': int,
        'subject': unicode,
        'tutor': unicode,
        'auditory': unicode,
        'subdivision': unicode,
        'type_': unicode
    }

    @classmethod
    def from_lesson(cls, group, lesson):
        o = GsqlGroupLesson()
        for f, conv in cls.IDENTITY_FIELDS.iteritems():
            setattr(o, f, conv(getattr(lesson, f)))
        o.faculty = group.faculty
        o.year = group.year
        o.group = group.group
        o.week_type = lesson.week_type.name
        return o

    def to_lesson(self):
        args = dict(((k, getattr(self, k)) for k in self.IDENTITY_FIELDS))
        args['week_type'] = self.week_type == 'upper' and UPPER_WEEK or LOWER_WEEK,
        return Lesson(*args)


class GsqlGroupDescriptor(db.Model):

    version = db.IntegerProperty()

    text = db.StringProperty()
    value = db.StringProperty()


class GsqlYearDescriptor(db.Model):

    version = db.IntegerProperty()

    text = db.StringProperty()
    value = db.StringProperty()


class GsqlFacultyDescriptor(db.Model):

    version = db.IntegerProperty()

    text = db.StringProperty()
    value = db.StringProperty()


class WeekSerializible(object):

    def set_id(self, id_data):
        raise NotImplementedError()

    @classmethod
    def from_data(cls, data):
        upper_week = data.week(UPPER_WEEK)
        lower_week = data.week(LOWER_WEEK)
        if not any((i[1] for i in upper_week)) and\
           not any((i[1] for i in lower_week)):
            return None
        obj = cls()
        obj.set_id(cls.get_id(data))
        obj._upper_week_data = cls._serialize_week(upper_week)
        obj._lower_week_data = cls._serialize_week(lower_week)
        return obj

    @classmethod
    def get_id(cls, proto):
        raise NotImplementedError()

    @classmethod
    def _serialize_day(cls, day):
        def conv_lesson(lesson):
            return {
                'week_day': lesson.week_day,
                'number': lesson.number,
                'subject': lesson.subject,
                'tutor': lesson.tutor,
                'auditory': lesson.auditory,
                'week_type': lesson.week_type.name,
                'subdivision': lesson.subdivision,
                'type_': lesson.type_
            }
        return [conv_lesson(lesson) for lesson in day.lessons() if lesson]

    @classmethod
    def _serialize_week(cls, data):
        return json.dumps([(wd, cls._serialize_day(day))
        for (wd, day) in data])

    @classmethod
    def _deserialize_day(cls, day):
        day_schedule = DaySchedule()
        for lesson_repr in day:
            lesson = Lesson(**lesson_repr)
            day_schedule.set_lesson(lesson.number, lesson)
        return day_schedule

    @classmethod
    def _deserialize_week(cls, data):
        repr = json.loads(data)
        return [(wd, cls._deserialize_day(day)) for wd, day in repr]

    def week(self, week_type):
        if week_type == UPPER_WEEK:
            if not self.__upper_week:
                self.__upper_week = self._deserialize_week(self._upper_week_data)
            return self.__upper_week
        else:
            if not self.__lower_week:
                self.__lower_week = self._deserialize_week(self._lower_week_data)
            return self.__lower_week


class GsqlClassroomData(db.Model, ClassroomData, WeekSerializible):

    version = db.IntegerProperty()

    building = db.StringProperty()
    number = db.StringProperty()

    _upper_week_data = db.TextProperty()
    _lower_week_data = db.TextProperty()

    def __init__(self, *args, **kwargs):
        super(GsqlClassroomData, self).__init__(*args, **kwargs)
        self.__upper_week = None
        self.__lower_week = None

    def classroom_id(self):
        return ClassroomId(self.building, self.number)

    def set_id(self, id_data):
        self.building = str(id_data.building)
        self.number = str(id_data.number)

    @classmethod
    def get_id(self, proto):
        return proto.classroom_id()


class GsqlGroupData(db.Model, GroupData, WeekSerializible):

    version = db.IntegerProperty()
    # contains only "value" from id dictionary
    faculty = db.StringProperty()
    year = db.StringProperty() # string for compatibility
    group = db.StringProperty()

    _upper_week_data = db.TextProperty()
    _lower_week_data = db.TextProperty()

    def group_id(self):
        return GroupId(self.faculty, self.year, self.group)

    def __init__(self, *args, **kwargs):
        super(GsqlGroupData, self).__init__(*args, **kwargs)
        self.__upper_week = None
        self.__lower_week = None

    def set_id(self, id_data):
        self.faculty = id_data.faculty
        self.year = id_data.year
        self.group = id_data.group

    @classmethod
    def get_id(cls, proto):
        return proto.group_id()


class GsqlDataSource(DataSource):

    """Base class for some source of schedule data"""

    def __init__(self, version=None):
        self.__forced_version = version
        self.version = None
        self.update_version()

    def update_version(self):
        old_version = self.version
        if not self.__forced_version:
            self.version = self.config_version() or self.latest_version()
        else:
            self.version = self.__forced_version
        if old_version != self.version:
            logging.debug('Using db version %s', self.version)

    def group_data(self, group_id):
        self.update_version()
        table = GsqlGroupData.all().filter('version =', self.version)\
                                   .filter('group =', group_id.group)\
                                   .filter('year =', group_id.year)\
                                   .filter('faculty =', group_id.faculty)\
                                   .fetch(1)
        for data in table:
            return data
        else:
            raise IndexError()

    def faculties(self):
        self.update_version()
        return [ {'text': f.text, 'value': f.value}
        for f in GsqlFacultyDescriptor.all()
                        .filter('version = ', self.version)
                        .order('text')]


    def years(self):
        self.update_version()
        return [ {'text': y.text, 'value': y.value}
        for y in GsqlYearDescriptor.all()
                        .filter('version = ', self.version)
                        .order('text')]

    def groups(self):
        self.update_version()
        return [ {'text': g.text, 'value': g.value}
        for g in GsqlGroupDescriptor.all()
                        .filter('version = ', self.version)
                        .order('text')]

    @classmethod
    def latest_version(cls, valid=True):
        if valid:
            versions = GsqlVersion.all().filter('valid =', True)\
                                        .order('-version').fetch(1)
        else:
            versions = GsqlVersion.all().order('-version').fetch(1)
        for v in versions:
            return v.version
        else:
            raise NoVersionStoredException()

    @classmethod
    def save_new_version(cls, groups, faculties, years, schedules):
        try:
            version = cls.latest_version(valid=False) + 1
        except NoVersionStoredException:
            version = 1
        timestamp = datetime.now()
        v = GsqlVersion(version=version, create_time=timestamp)
        v.put()
        def save_class(class_, list):
            for item in list:
                o = class_(version=version, text=item['text'],
                    value=item['value'])
                o.put()
        save_class(GsqlGroupDescriptor, groups)
        save_class(GsqlFacultyDescriptor, faculties)
        save_class(GsqlYearDescriptor, years)
        cls._save_groups(version, schedules)
        cls._save_classrooms(version, schedules)
        v.valid = True
        v.put()
        return version

    @classmethod
    def _save_groups(cls, version, schedules):
        for data in schedules:
            group_data = GsqlGroupData.from_data(data)
            group_data.version = version
            if group_data:
                group_data.put()

    @classmethod
    def _save_classrooms(cls, version, schedules):
        # [ clsrm -> [week_type -> [day -> day_schedule]] ]
        classrooms = AutoaddDict(
            lambda _: AutoaddDict(
                lambda _: AutoaddDict(
                    lambda _: DaySchedule())))
        for data in schedules:
            def process_week(wtype):
                week_data = data.week(wtype)
                for (day_id, day) in week_data:
                    for lesson in day.list():
                        clsdata = \
                            classrooms[lesson.classroom_id][wtype][day_id]
                        clsdata.set_lesson(lesson.number, lesson)
            process_week(UPPER_WEEK)
            process_week(LOWER_WEEK)
        def conv(lst):
            p = lst.items()
            p.sort(lambda t1, t2: cmp(t1[0], t2[0]))
            return [ i for i in p if len(i[1])>0 ]
        for (room_id, wdata) in classrooms.items():
            data = ClassroomDataContainer(room_id,
                                          conv(wdata[UPPER_WEEK]),
                                          conv(wdata[LOWER_WEEK]))
            classroom_data = GsqlClassroomData.from_data(data)
            classroom_data.version = version
            classroom_data.put()

    @classmethod
    def config_version(cls):
        for vers in GsqlStoreConfiguration.all():
            return vers.current_version
        else:
            config = GsqlStoreConfiguration(current_version=0)
            config.put()
            return 0