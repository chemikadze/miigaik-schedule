# -*- coding: utf-8 -*-

import json
import time
import logging

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound

import api_v2
import settings
from sources import CURRENT_SOURCE, CURRENT_TIMETABLE
from sources.datamodel import GroupId, UPPER_WEEK, LOWER_WEEK


class with_args:

    def __init__(self, *argnames):
        self.argnames = argnames

    def __call__(self, f):
        def wrapped(request):
            kwargs = {}
            for name in self.argnames:
                if name in request.GET:
                    kwargs[name] = request.GET[name]
                else:
                    return HttpResponseBadRequest(
                        "Required query arguments are: " +
                        ", ".join(self.argnames))
            return f(request, **kwargs)
        return wrapped


def json_response(response_data):
    return HttpResponse(
        json.dumps(response_data, ensure_ascii=False, encoding='UTF-8'),
        content_type="application/json; charset=utf-8")


def api_v2_upload(request):
    source = CURRENT_SOURCE()
    logging.info("Uploading version %s" % source.version)
    start = time.clock()
    data = api_v2.generate_data(source)
    api_v2.upload_data(data, settings.RASP_VUZOV_TOKEN, settings.RASP_VUZOV_ADMIN)
    logging.debug("Upload finished, took %s ms" % ((time.clock() - start) * 1000))
    return json_response(data)


def index(request):
    data_version = CURRENT_SOURCE().latest_version_object()
    return json_response({
        "last_data_update": data_version.create_time.strftime("%Y-%m-%d %H:%M:%S UTC"), # TODO: bound to GsqlDatastore
        "mailto": "chemikadze@gmail.com",
        "source_code": "https://github.com/chemikadze/miigaik-schedule",
        "target": "http://raspisaniye-vuzov.ru",
        "spec": "https://docs.google.com/document/d/1BPZkBa5Y_gcGj25Q3eVm7Ftxh0_NG4a1DYhKR-jjfNQ/edit?pli=1#"
    })


def get_faculties(request):
    faculties = CURRENT_SOURCE().faculties()
    response_data = {
        "faculties": map(faculty_to_json, faculties)
    }
    return json_response(response_data)


@with_args('faculty_id')
def get_groups(request, faculty_id):
    group_names = dict(map(
        lambda g: (g['value'], g['text']),
        CURRENT_SOURCE().groups()))
    filtered_groups = CURRENT_SOURCE().groups_data(faculty_id=faculty_id)
    groups = {}
    for group in filtered_groups:
        full_id = pack_group_id(group.group_id())
        groups[full_id] = group_names[group.group_id().group]
    response_data = {
        "groups": map(group_to_json, groups.items())
    }
    return json_response(response_data)


@with_args('group_id')
def get_schedule(request, group_id):
    try:
        id = unpack_group_id(group_id)
    except:
        return HttpResponseBadRequest("Group id should have format: faculty|year|groupname")
    try:
        response_data = group_data_to_json(CURRENT_SOURCE().group_data(id))
    except IndexError:
        return HttpResponseNotFound("Can not find group: " + group_id)
    return json_response(response_data)


def faculty_to_json(faculty):
    return {
        "faculty_name": faculty["text"],
        "faculty_id": faculty["value"],
        "date_start": None,
        "date_end": None
    }


def group_to_json(tuple):
    (group_id, group_name) = tuple
    return {
        "group_id": group_id,
        "group_name": group_name
    }


def pack_group_id(group_id):
    return "%(faculty)s|%(year)s|%(group)s" % group_id.__dict__


def unpack_group_id(group_id):
    [faculty, year, group] = group_id.split("|")
    return GroupId(faculty, year, group)


WEEK_PARITY = {
    UPPER_WEEK.name: 1,
    LOWER_WEEK.name: 2
}

LESSON_TYPE = {
    u"лекция": 2,
    u"практика": 0
}


def classroom_id_to_name(id):
    if id.building == '1':
        return id.number
    else:
        return u"%s к%s" % (id.number, id.building)


def lesson_type_from_string(typename):
    return LESSON_TYPE.get(typename.strip(), 0)


def lesson_to_json(lesson):
    timetable = CURRENT_TIMETABLE()
    return {
        "subject": lesson.subject,
        "type": lesson_type_from_string(lesson.type_),
        "time_start": timetable.start(lesson.number).strftime("%H:%M"),
        "time_end": timetable.end(lesson.number).strftime("%H:%M"),
        "parity": WEEK_PARITY[lesson.week_type],
        "date_start": None,
        "date_end": None,
        "dates": None,
        "teachers": [ { "teacher_name": lesson.tutor } ],
        "auditories": [
            {
                "auditory_name": classroom_id_to_name(lesson.classroom_id),
                "auditory_address": None
            }
        ]
    }


def group_data_to_json(data):

    weekdays = {}

    for week_type in [UPPER_WEEK, LOWER_WEEK]:
        for (weekday, schedule) in data.week(week_type):
            for lesson in schedule.list():
                lst = weekdays.get(weekday, list())
                lst.append(lesson)
                weekdays[weekday] = lst

    days = map(
        lambda (n, l): {"weekday": n, "lessons": map(lesson_to_json, l)},
        weekdays.items())

    return {
        "group_name": "группа 1",
        "days": days
    }
