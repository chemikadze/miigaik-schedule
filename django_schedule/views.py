from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.shortcuts import render_to_response
from django import forms
from logging import getLogger
from django.template.defaultfilters import register

logger = getLogger('views')

from sources import CURRENT_SOURCE
from sources.datamodel import GroupId, UPPER_WEEK, LOWER_WEEK, DaySchedule, MAP_DAY_STR
from sources.util import *

SOURCE = CURRENT_SOURCE()


@register.filter
def get_week(day):
    return MAP_DAY_STR[int(day.week_day)]


class SelectGroupFrom(forms.Form):

    faculty = forms.ChoiceField()
    year = forms.ChoiceField()
    group = forms.ChoiceField()

    def __init__(self, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        self.fields['faculty'].choices = [(x, x) for x in SOURCE.faculties()]
        self.fields['year'].choices = [(x, x) for x in SOURCE.years()]
        self.fields['group'].choices = [(x, x) for x in SOURCE.groups()]


def home(request):
    form = SelectGroupFrom()
    return render_to_response('desktop/home.html', {'form': form})


def main_handler(request):
    # TODO: correct show urls
    return HttpResponseRedirect('/schedule/%(faculty)s/%(year)s/%(group)s/'
        % request.GET)


def week_schedule(request, faculty, year, group, week=None):
    group_data = SOURCE.group_data(GroupId(faculty, year, group))
    if week is None:
        week_data = [day for day in
                     merged_weeks(group_data.week(UPPER_WEEK),
                                  group_data.week(LOWER_WEEK))]
    else:
        week_data = [day.list() for (_, day) in group_data.week(week)]
    descr = 'TODO'
    logger.debug('data: %s', week_data)
    return render_to_response('desktop/days.html', {'days': week_data,
                                                    'schedule_descr': descr})


def day_schedule(request, faculty, year, group, day, week=None):
    day = int(day)
    group_data = SOURCE.group_data(GroupId(faculty, year, group))
    def pred(x):
        return x[0] == day
    no_day = (-1, DaySchedule())
    if week is None:
        first = locate(group_data.week(UPPER_WEEK), pred, no_day)[1]
        second = locate(group_data.week(LOWER_WEEK), pred, no_day)[1]
        if first and second:
            day = merged_days(first, second)
        else:
            day = (first or second).list()
    else:
        day = locate(group_data.week(week), pred, no_day)[1].list()
    week_data = [day]
    descr = 'TODO'
    return render_to_response('desktop/days.html', {'days': week_data,
                                                    'schedule_descr': descr})