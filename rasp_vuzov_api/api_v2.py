# -*- coding: utf-8 -*-

import json
import urllib
import urllib2
import urlparse
import logging
from datetime import date
from StringIO import StringIO

import requests

from sources.datamodel import UPPER_WEEK, LOWER_WEEK
from sources import util
from sources.versions import CURRENT_TIMETABLE

STANDARD_ENDPOINT = "http://api.rvuzov.ru/v2/import"
MULTIPART_ENDPOINT = "http://api.rvuzov.ru/v2/import/file"


def upload_data(data, token, report, multipart=False):
    _upload_file(data, token, report)


# GAE refuses to make requests with URL that large, not used
def _upload_url(data, token, report):
    payload = json.dumps(data, ensure_ascii=False)
    logging.debug(payload)
    logging.info("uploading %s bytes" % len(payload))
    template = urlparse.urlparse(STANDARD_ENDPOINT)
    url_obj = template._replace(query=urllib.urlencode({
        "type": "json",
        "data": payload.encode("utf-8"),
        "token": token,
        "report": report
    }))
    url = urlparse.urlunparse(url_obj)
    r = requests.post(url)
    logging.info("Response:\n" + r.text)


def _upload_file(data, token, report):
    payload = json.dumps(data, ensure_ascii=False)
    logging.debug(payload)
    logging.info("uploading %s bytes" % len(payload))
    template = urlparse.urlparse(MULTIPART_ENDPOINT)
    url_obj = template._replace(query=urllib.urlencode({
        "type": "json",
        "datafile": "file",
        "token": token,
        "report": report
    }))
    url = urlparse.urlunparse(url_obj)
    files = {"file": StringIO(payload)}
    r = requests.post(url, files=files)
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


def unfold_week(week_type, week_data):
    acc = []
    today = date.today()
    if today.month < 8 and today.day < 20:
        lessons_begin = date(today.year, 2, 10)
        lessons_end = date(today.year, 5, 31)
    else:
        lessons_begin = date(today.year, 9, 1)
        lessons_end = date(today.year, 12, 31)

    if (util.current_week() == LOWER_WEEK) == bool(date.today().isocalendar()[1] % 2):
        week = 1 + int(util.current_week() == UPPER_WEEK)
    else:
        week = 1 + int(util.current_week() == LOWER_WEEK)
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

