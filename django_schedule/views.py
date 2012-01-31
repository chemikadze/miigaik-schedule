# -:- coding: utf-8 -:-

from django.http import HttpResponse, HttpRequest, HttpResponseRedirect, Http404, HttpResponseNotFound
from django.shortcuts import render_to_response
from django import forms
from logging import getLogger
from django.template.defaultfilters import register
from time import localtime, strftime
from django.template import RequestContext

logger = getLogger('views')

from sources import CURRENT_SOURCE
from sources.datamodel import GroupId, UPPER_WEEK, LOWER_WEEK, DaySchedule, MAP_DAY_STR
from sources.util import *

SOURCE = CURRENT_SOURCE()

WEEK_NAME_MAP = {'upper': UPPER_WEEK, 'lower': LOWER_WEEK, 'both': None}
WEEK_NAME_MAP_RU = {'upper': u'верхняя', 'lower': u'нижняя',
                    'both': u'верняя и нижняя'}


def render_response(request, template, *args, **kwargs):
    response = render_to_response(get_template(request, template),
        *args,
        context_instance=RequestContext(request),
        **kwargs)
    iface = request.GET.get('iface')
    if iface:
        response.set_cookie('iface', iface, max_age=365*24*60*60)
    return response


def localized_week(week_txt):
    try:
        return WEEK_NAME_MAP_RU[week_txt]
    except KeyError:
        week = current_week()
        return localized_week(week.name)


def week_from_txt(week_txt):
    try:
        return WEEK_NAME_MAP[week_txt]
    except KeyError:
        if week_txt == 'current':
            return current_week()
        else:
            raise

@register.filter
def get_weekday(day):
    return MAP_DAY_STR[int(day.week_day)]


@register.filter
def get_weekday_id(day):
    return day.week_day

@register.filter
def is_today(day):
    return str(day) == str(current_weekday())


def get_template(request, name):
    forced = request.GET.get('iface') or request.COOKIES.get('iface')
    if forced:
        if forced == "mobile":
            return 'mobile/' + name
        else:
            return 'desktop/' + name
    else:
        for fp in ('Android', 'iPhone', 'iPod'):
            if fp in request.META['HTTP_USER_AGENT']:
                return 'mobile/' + name
        return 'desktop/' + name


class SelectGroupFrom(forms.Form):

    faculty = forms.ChoiceField(label="Факультет")
    year = forms.ChoiceField(label="Курс")
    group = forms.ChoiceField(label="Группа")

    def __init__(self, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        def itemize(x):
            return x['value'], x['text']
        self.fields['faculty'].choices = [itemize(x) for x in SOURCE.faculties()]
        self.fields['year'].choices = [itemize(x) for x in SOURCE.years()]
        self.fields['group'].choices = [itemize(x) for x in SOURCE.groups()]


def home(request):
    form = SelectGroupFrom()
    return render_response(request, 'home.html', {'form': form})


def main_handler(request):
    return HttpResponseRedirect('/schedule/%(faculty)s/%(year)s/%(group)s/current'
        % request.GET)


def today(request, faculty, year, group):
    week_txt = current_week().name
    day_txt = current_weekday()
    schedule = create_schedule_common(request, faculty, year, group, week_txt, day_txt)
    schedule['today'] = True
    return render_response(request, 'days.html', schedule)


def create_schedule_common(request, faculty, year, group, week_txt, day_txt=None):
    day = day_txt and int(day_txt) or -1
    group_data = SOURCE.group_data(GroupId(faculty, year, group))
    try:
        week = week_from_txt(week_txt)
        week_txt_ru = localized_week(week_txt)
    except KeyError:
        raise Http404()

    def week_create(week):
        def pred(x):
            return x[0] == day
        day_data = locate(week, pred)
        if day_data is None:
            return []
        else:
            return [day_data]

    if week is None:
        if day >= 0:
            first = week_create(group_data.week(UPPER_WEEK))
            second = week_create(group_data.week(LOWER_WEEK))
        else:
            first = group_data.week(UPPER_WEEK)
            second = group_data.week(LOWER_WEEK)
        week_data = merged_weeks(first, second)
    else:
        raw_week_data = group_data.week(week)
        if day >= 0:
            week_data = [d.list() for (_, d) in week_create(raw_week_data)]
        else:
            week_data = [day.list() for (_, day) in raw_week_data]
    week_data = [d for d in week_data if d]
    if not week_data:
        lessons = [0]
    else:
        lessons = map(len, week_data)
    stats = {'days': len(week_data),
             'lessons': sum(lessons),
             'avg_lessons': sum(lessons)/len(lessons),
             'min_lessons': min(lessons),
             'max_lessons': max(lessons)}
    return {'days': week_data,
            'faculty': faculty,
            'year': year,
            'group': group,
            'week_url': week_txt,
            'day': day_txt,
            'week_ru': week_txt_ru,
            'stats': stats}

def schedule_common(request, faculty, year, group, week_txt, day_txt=None):
    return render_response(request, 'days.html',
        create_schedule_common(request, faculty, year, group, week_txt, day_txt))