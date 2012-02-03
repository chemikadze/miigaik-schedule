from datetime import datetime
import json
from google.appengine.ext import db
from sources.datamodel import Lesson, LOWER_WEEK, UPPER_WEEK, DaySchedule, GroupData, GroupId
from sources.site import GroupDataContainer
import logging


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


class GsqlGroupData(db.Model, GroupData):

    version = db.IntegerProperty()
    # contains only "value" from id dictionary
    faculty = db.StringProperty()
    year = db.StringProperty() # string for compatibility
    group = db.StringProperty()

    _upper_week_data = db.TextProperty()
    _lower_week_data = db.TextProperty()

    def group_id(self):
        return GroupId(self.faculty, self.year, self.group)

    def week(self, week_type):
        if week_type == UPPER_WEEK:
            if not self.__upper_week:
                self.__upper_week = self._deserialize_week(self._upper_week_data)
            return self.__upper_week
        else:
            if not self.__lower_week:
                self.__lower_week = self._deserialize_week(self._lower_week_data)
            return self.__lower_week

    def __init__(self, *args, **kwargs):
        super(GsqlGroupData, self).__init__(*args, **kwargs)
        self.__upper_week = None
        self.__lower_week = None

    @classmethod
    def from_group_data(cls, group_data):
        upper_week = group_data.week(UPPER_WEEK)
        lower_week = group_data.week(LOWER_WEEK)
        if not any((i[1] for i in upper_week)) and \
           not any((i[1] for i in lower_week)):
            return None
        obj = GsqlGroupData()
        obj.faculty = group_data.group_id().faculty
        obj.year = group_data.group_id().year
        obj.group = group_data.group_id().group
        obj._upper_week_data = cls._serialize_week(upper_week)
        obj._lower_week_data = cls._serialize_week(lower_week)
        return obj

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




class GsqlDataSource(object):

    """Base class for some source of schedule data"""

    def __init__(self, version=None):
        config_version = self.config_version()
        if not version:
            version = config_version or self.latest_version()
        self.version = version
        logging.debug('Using db version %s', self.version)

    def group_data(self, group_id):
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
        return [ {'text': f.text, 'value': f.value}
        for f in GsqlFacultyDescriptor.all()
                        .filter('version = ', self.version)
                        .order('text')]


    def years(self):
        return [ {'text': y.text, 'value': y.value}
        for y in GsqlYearDescriptor.all()
                        .filter('version = ', self.version)
                        .order('text')]

    def groups(self):
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
        for data in schedules:
            group_data = GsqlGroupData.from_group_data(data)
            group_data.version = version
            if group_data:
                group_data.put()
        v.valid = True
        v.put()
        return version

    @classmethod
    def config_version(cls):
        for vers in GsqlStoreConfiguration.all():
            return vers.current_version
        else:
            config = GsqlStoreConfiguration(current_version=0)
            config.put()
            return 0