# -:- coding: utf-8 -:-
import json

from logging import getLogger

from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.shortcuts import render_to_response
from django import forms
from django.template.defaultfilters import register
from django.template import RequestContext, TemplateSyntaxError
from django.views.decorators.vary import vary_on_headers


logger = getLogger('views')

from sources import CURRENT_SOURCE, CURRENT_TIMETABLE
from sources.datamodel import GroupId, MAP_DAY_STR, UPPER_WEEK, LOWER_WEEK
from sources.util import current_week, current_weekday, locate, merged_weeks, \
    group_data_to_ical, current_lesson, AutoaddDict, cid_cmp

SOURCE = CURRENT_SOURCE()

WEEK_NAME_MAP = {'upper': UPPER_WEEK, 'lower': LOWER_WEEK, 'both': None}
WEEK_NAME_MAP_RU = {'upper': u'верхняя', 'lower': u'нижняя',
                    'both': u'верняя и нижняя'}


def render_response(request, template, *args, **kwargs):
    response = \
        render_to_response(get_template(request, template),
                           context_instance=RequestContext(request),
                           *args, **kwargs)
    iface = request.GET.get('iface')
    if iface:
        response.set_cookie('iface', iface, max_age=365 * 24 * 60 * 60)
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


@register.filter
def urlencodeall(url):
    from django.utils.http import urlquote
    return urlquote(url, '')


@register.tag
def urle(parser, token):
    from django.template.defaulttags import kwarg_re, URLNode
    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("'%s' takes at least one argument"
                                  " (path to a view)" % bits[0])
    viewname = bits[1]
    args = []
    kwargs = {}
    asvar = None
    bits = bits[2:]

    if len(bits):
        for bit in bits:
            match = kwarg_re.match(bit)
            if not match:
                raise TemplateSyntaxError("Malformed arguments to url tag")
            name, value = match.groups()
            if name:
                kwargs[name] = parser.compile_filter(value + '|urlencodeall')
            else:
                args.append(parser.compile_filter(value))
    return URLNode(viewname, args, kwargs, asvar)


def present_classroomid(id):
    if id.building == '1':
        return id.classroom
    else:
        return u"%s к%s" % (id.classroom, id.building)


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

        self.fields['faculty'].choices = \
            [itemize(x) for x in SOURCE.faculties()]
        self.fields['year'].choices = [itemize(x) for x in SOURCE.years()]
        self.fields['group'].choices = [itemize(x) for x in SOURCE.groups()]


class FindFreeClassroomsForm(forms.Form):

    building = forms.ChoiceField(label="Здание")
    week = forms.ChoiceField(
        [(v, WEEK_NAME_MAP_RU[v])
         for v in ('upper', 'lower')], label="Неделя")
    day = forms.ChoiceField(
        [(i, i) for i in xrange(1, 7)], label="День")
    lesson = forms.ChoiceField(
        [(i, i) for i in xrange(1, 10)], label="Начиная с пары")
    length = forms.ChoiceField(
        [(i, i) for i in xrange(1, 10)], label="Продолжительность, пар")

    def __init__(self, *args, **kwargs):
        super(forms.Form, self).__init__(*args, **kwargs)
        self.fields['building'].choices = [('*', "Любое")] + \
            [(i, i) for i in SOURCE.buildings()]


@vary_on_headers('User-Agent', 'Cookie')
def home(request):
    form = SelectGroupFrom()
    return render_response(request, 'home.html', {'form': form})


@vary_on_headers('User-Agent', 'Cookie')
def main_handler(request):
    from django.core.urlresolvers import reverse, NoReverseMatch
    try:
        return HttpResponseRedirect(
            reverse('django_schedule.views.generic_schedule_common',
                    kwargs=dict(x for x in request.GET.items()
                                if x[0] in ('faculty', 'year', 'group'))))
    except NoReverseMatch:
        return HttpResponseRedirect("/")


@vary_on_headers('User-Agent', 'Cookie')
def generic_today(request, method, id_factory, template, **data_id):
    week_txt = current_week().name
    day_txt = current_weekday()
    schedule = create_schedule_common(method, id_factory,
                                      week_txt, day_txt, **data_id)
    schedule['today'] = True
    return render_response(request, 'days_%s.html' % template, schedule)


def create_schedule_common(method, id_method, week_txt, day_txt=None,
                           **id_data):
    day = day_txt and int(day_txt) or -1
    try:
        group_id = id_method(**id_data)
        group_data = getattr(SOURCE, method)(group_id)
        week = week_from_txt(week_txt)
        week_txt_ru = localized_week(week_txt)
    except (KeyError, IndexError):
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
             'avg_lessons': sum(lessons) / len(lessons),
             'min_lessons': min(lessons),
             'max_lessons': max(lessons)}
    data = {'days': week_data,
            'week_url': week_txt,
            'day': day_txt,
            'week_ru': week_txt_ru,
            'current_week_url': current_week().name,
            'current_week_ru': localized_week(current_week().name),
            'dataset_id': group_id,
            'stats': stats,
            }
    return data


@vary_on_headers('User-Agent', 'Cookie')
def generic_schedule_common(request, method, id_factory, week_txt, template,
                            day_txt=None, **data_id):
    return render_response(
        request, 'days_%s.html' % template,
        create_schedule_common(method, id_factory, week_txt, day_txt,
                               **data_id))


@vary_on_headers('User-Agent', 'Cookie')
def icalendar_common(request, method, id_factory, week_txt, day_txt=None,
                     **id_data):
    del id_data['template']
    try:
        group_id = id_factory(**id_data)
        group_data = getattr(SOURCE, method)(group_id)
    except (KeyError, IndexError):
        raise Http404()

    def pred(lesson):
        return ((week_txt in ('both', 'current')
                 or lesson.week_type == week_txt)) and \
               (not day_txt
                or str(lesson.week_day) == day_txt
                or (lesson.week_day == current_weekday()
                    and day_txt == 'today'))

    ical = group_data_to_ical(group_data, CURRENT_TIMETABLE(), pred)
    response = HttpResponse(
        ical.as_string(), mimetype='text/calendar; charset=utf-8')
    filename = u'schedule.ics'

    def trans(i):
        if i > 128:
            return i - 128
        else:
            return i

    translated = ''.join(
        [chr(trans(ord(i))) for i in filename.encode('koi8-r')])
    response['Content-Disposition'] = 'attachment; filename=%s' % translated
    return response


@vary_on_headers('User-Agent', 'Cookie')
def free_classrooms(request):
    conv = lambda x: x != '*' and x or None
    curr = current_lesson() or 1
    frm = int(request.GET.get('lesson', curr))
    len = int(request.GET.get('length', 1))
    timestamp = {
        'week': request.GET.get('week', current_week().name),
        'building': conv(request.GET.get('building', '*')),
        'day': int(request.GET.get('day', current_weekday())),
        'lessons': range(frm, frm + len)
    }
    buildings = AutoaddDict(lambda _: list())
    for classroom in SOURCE.free_classrooms(**timestamp):
        buildings[classroom.building].append(classroom)
    buildings = sorted(buildings.iteritems(), cmp=lambda a, b: cmp(a[0], b[0]))
    fbuildings = map(lambda x: {'name': x[0],
                                'classrooms': sorted(x[1], cmp=cid_cmp)},
                     buildings)
    inits = dict(request.GET.items())
    inits.update(timestamp)
    inits['lesson'] = frm
    data = {'form': FindFreeClassroomsForm(initial=inits),
            'buildings': fbuildings,
            'week_txt': timestamp['week']}
    return render_response(request, 'free_classrooms.html', data)


def json_response(response_data):
    return HttpResponse(
        json.dumps(response_data, ensure_ascii=False, encoding='UTF-8'),
        content_type="application/json; charset=utf-8")


def list_groups(request, faculty, year):
    data = SOURCE.groups(faculty, year)
    result = {}
    for item in data:
        result[item['value']] = item['text']
    return json_response({'groups': result})
