# -*- coding: utf-8 -*-

import json
import logging
from StringIO import StringIO
from datetime import date

import requests
from sources import util
from sources.datamodel import UPPER_WEEK, LOWER_WEEK
from sources.versions import CURRENT_TIMETABLE

STANDARD_ENDPOINT = "http://api.rvuzov.ru/v2/import"
MULTIPART_ENDPOINT = "http://api.rvuzov.ru/v2/import/file"


def upload_data(data, token, report, multipart=False):
    _upload_field(data, token, report)


def _upload_field(data, token, report):
    payload = json.dumps(data, ensure_ascii=False)
    logging.debug(payload)
    logging.info("uploading %s bytes" % len(payload))
    r = requests.post(STANDARD_ENDPOINT,
                      data={
                          "type": "json",
                          "data": payload.encode("utf-8"),
                          "token": token,
                          "report": report
                      })
    logging.info("Response:\n" + r.text)


def _upload_file(data, token, report):
    payload = json.dumps(data, ensure_ascii=False)
    logging.debug(payload)
    logging.info("uploading %s bytes" % len(payload))
    r = requests.post(MULTIPART_ENDPOINT,
                      data={
                          "type": "json",
                          "token": token,
                          "report": report
                      },
                      files={
                          "datafile": StringIO(payload)
                      })
    logging.info("Response:\n" + r.text)


def generate_data(source):
    return {
        "faculties": generate_faculties(source),
        "name": u"Московский Государственный Университет Геодезии и Картографии",
        "abbr": u"МИИГАиК"
    }


def generate_faculties(source):
    acc = []
    for faculty in source.faculties():
        generated = {
            "name": faculty["text"],
            "groups": generate_groups(source.groups_data(faculty_id=faculty['value']))
        }
        acc.append(generated)
    return acc


def generate_groups(groups_data):
    acc = []
    for group in groups_data:
        id = group.group_id()
        generated = {
            "lessons": unfold_week(UPPER_WEEK, group.week(UPPER_WEEK)) +
                       unfold_week(LOWER_WEEK, group.week(LOWER_WEEK)),
            "name":  id.group
        }
        acc.append(generated)
    return acc


def _rasp_vuzov_week_number(input_date):
    if date(input_date.year, input_date.month, 1).isocalendar()[1] != 1:
        # check if isocalendar thinks it's last year's week
        if input_date.isocalendar()[0] != input_date.year:
            return 1
        else:
            return input_date.isocalendar()[1] + 1
    else:
        return input_date.isocalendar()[1]


def _week_type_to_number(week_type):
    if (util.current_week() == LOWER_WEEK) == bool(_rasp_vuzov_week_number(date.today()) % 2):
        # upper week is even
        week = 1 + int(week_type == UPPER_WEEK)
    else:
        # else lower week is even
        week = 1 + int(week_type == LOWER_WEEK)
    return week


def unfold_week(week_type, week_data):
    acc = []
    today = date.today()
    if today < today.replace(month=8, day=20):
        lessons_begin = date(today.year, 2, 10)
        lessons_end = date(today.year, 5, 31)
    else:
        lessons_begin = date(today.year, 9, 1)
        lessons_end = date(today.year, 12, 31)

    week = _week_type_to_number(week_type)
    for (weekday, schedule) in week_data:
        for lesson in schedule.list():
            generated = {
                "teachers": [{"name": lesson.tutor}],
                "subject": lesson.subject,
                "type": lesson.type_,
                "time": {
                    "start": CURRENT_TIMETABLE().start(lesson.number).strftime("%H:%M"),
                    "end": CURRENT_TIMETABLE().end(lesson.number).strftime("%H:%M")
                },

                "date": {
                    "start": lessons_begin.strftime("%d.%m.%Y"),
                    "end": lessons_end.strftime("%d.%m.%Y"),
                    "weekday": weekday,
                    "week": week
                },
                "audiences": [{"name": u"%s к%s" % (lesson.classroom_id.number, lesson.classroom_id.building)}]
            }
            if lesson.subdivision.strip():
                generated["subgroups"] = lesson.subdivision.strip()
            acc.append(generated)
    return acc
