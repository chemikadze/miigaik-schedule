#!/usr/bin/env python

import sys
import httplib
import os
from urlparse import urlsplit, urlunsplit
from cgi import parse_qs, parse_qsl
from xml.dom import minidom
import re
from pyexpat import ExpatError

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util
from google.appengine.ext import db
from google.appengine.runtime import DeadlineExceededError


MIIGAIK_SCHEDULE_URL = 'http://studydep.miigaik.ru/semestr/index.php'
MIIGAIK_HOSTNAME, MIIGAIK_SCHEDULE_PATH = urlsplit(MIIGAIK_SCHEDULE_URL)[1:3]
REQUEST_TIMEOUT = 120

class RequestError(Exception):
    def __init__(self, descr, response, body):
        super(Exception, self).__init__()
        self.descr = descr
        self.response = response
        self.body = body

    def __str__(self):
        return 'RequestError %s: <br/>HTTPResponse: %sReply from server: %s' % (self.descr, self.response, self.body)


def render_template(template_name, context=dict()):
    self_root = os.path.dirname(__file__)
    template_path = os.path.join(self_root, template_name)
    return template.render(template_path, context)

def request_post(url, parameters=dict(), headers=dict()):
    spliturl = urlsplit(url)
    host = spliturl.hostname
    port = spliturl.port
    http = httplib.HTTPConnection(host, port, timeout=REQUEST_TIMEOUT)
    post_data = '&'.join('%s=%s' % parameter for parameter in parameters.items())
    try:
        http.request('POST', url, body=post_data, headers=headers)
        resp = http.getresponse()
        body = resp.read()
    except DeadlineExceededError:
        raise RequestError('Can not perform request: time exceed. Please try later', None, '')
    if resp.status == 200:
        return resp, body
    else:
        raise RequestError('Error requesting page', resp, body)


def polite(f):
    def wrapper(*argv):
        try:
            f(*argv)
        except RequestError, e:
            print render_template('templates/request_error.html', {'error': e})
        except Exception, e:
            print render_template('templates/request_error.html', {'error': e})
    return wrapper

class ShortcutHandler(webapp.RequestHandler):
    def render_to_response(self, template_name, context=dict()):
        self.response.out.write(render_template(template_name, context))


class MainHandler(ShortcutHandler):
    @polite
    def get(self):
        url = MIIGAIK_SCHEDULE_URL
        spliturl = urlsplit(url)
        host = spliturl.hostname
        port = spliturl.port
        path = spliturl[2]
        http = httplib.HTTPConnection(host, port, timeout=REQUEST_TIMEOUT)
        try:
            http.request('GET', path)
            resp = http.getresponse()
            body_data = resp.read().decode('cp1251').encode('utf8')
            result = re.findall(r'(<form.*form>)', body_data, re.S) # fucking php fans don't gimme valid html
            form_body = result[0]
            form_body = re.sub(r'action="index.php"', 'action="/link"', form_body)
            form_body = re.sub(r'method="post"', 'metod="GET"', form_body)
        except DeadlineExceededError:
            raise RequestError('Can not perform request: time exceed. Please try later', None, '')
        except (IndexError, ExpatError), e:
            raise RequestError('Can not load form data: malformed web page', None, '')
        self.render_to_response('templates/main.html', {'form': form_body})


class RedirectHandler(webapp.RequestHandler):
    @polite
    def get(self):
        scheme, netloc, path, query, fragment = urlsplit(self.request.url)
        netloc = MIIGAIK_HOSTNAME # TODO: use referer here
        url = urlunsplit((scheme, netloc, path, query, fragment))
        self.redirect(url)


class LinkHandler(ShortcutHandler):
    @polite
    def get(self): # TODO: JS!
        query_u = parse_qs(self.request.query_string)
        query = dict((k, u[0].decode('utf8').encode('cp1251')) for k, u in query_u.items())
        try:
            resp, body = request_post(MIIGAIK_SCHEDULE_URL, query, {'referer': self.request.url})
        except RequestError, e:
            self.render_to_response('templates/request_error.html', {'error': e})
            return
        self.response.out.write(body.decode('cp1251').encode('utf8'))


def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/link', LinkHandler),
                                          ('/.*', RedirectHandler)],
                                         debug=False)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
