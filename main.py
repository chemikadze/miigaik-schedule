#!/usr/bin/env python

import httplib
import os
from urlparse import urlsplit, urlunsplit
from cgi import parse_qs, parse_qsl

from google.appengine.ext import webapp
from google.appengine.ext.webapp import template, util
from google.appengine.ext import db
from google.appengine.runtime import DeadlineExceededError


MIIGAIK_SCHEDULE_URL = 'http://studydep.miigaik.ru/semestr/index.php'
MIIGAIK_HOSTNAME = urlsplit(MIIGAIK_SCHEDULE_URL)[1]
REQUEST_TIMEOUT = 120

class RequestError(Exception):
    def __init__(self, descr, response, body):
        super(Exception, self).__init__()
        self.descr = descr
        self.response = response
        self.body = body

    def __str__(self):
        return 'RequestError %s: HTTPResponse: %s\nReply from server: %s' % (self.descr, self.response, self.body)


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


class ShortcutHandler(webapp.RequestHandler):
    def render_to_response(self, template_name, context=dict()):
        self.response.out.write(render_template(template_name, context))


class MainHandler(ShortcutHandler):
    def get(self):
        self.render_to_response('templates/main.html')


class RedirectHandler(webapp.RequestHandler):
    def get(self):
        scheme, netloc, path, query, fragment = urlsplit(self.request.url)
        netloc = MIIGAIK_HOSTNAME # TODO: use referer here
        url = urlunsplit((scheme, netloc, path, query, fragment))
        self.redirect(url)


class LinkHandler(ShortcutHandler):
    def get(self): # TODO: JS!
        query_u = parse_qs(self.request.query_string)
        query = dict((k, u[0].decode('utf8').encode('cp1251')) for k, u in query_u.items())
        try:
            resp, body = request_post(MIIGAIK_SCHEDULE_URL, query, {'referer':self.request.url})
        except RequestError, e:
            self.render_to_response('templates/request_error.html', {'error':e})
            return
        self.response.out.write(body.decode('cp1251').encode('utf8'))


def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/link', LinkHandler),
                                          ('/.*', RedirectHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
