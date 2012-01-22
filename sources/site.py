import urllib
import urllib2

from datamodel import GroupData
from sources.datamodel import UPPER_WEEK

REQUEST_TOUT = 120


class RequestError(Exception):
    def __init__(self, descr, response, body):
        super(Exception, self).__init__()
        self.descr = descr
        self.response = response
        self.body = body

    def __str__(self):
        return 'RequestError: %s <br/>HTTPResponse: %s<br/>Reply from server: %s' %\
               (self.descr, self.response, self.body)


class FormatError(Exception):

    def __init__(self, where, reason):
        super(Exception, self).__init__(
            'Can not parse format on url "%s" with reason "%s"'
                % (where, reason))


def request_post(url, parameters=dict()):
    post_data = '&'.join('%s=%s' % parameter for parameter in parameters.items())
    return urllib2.urlopen(url, post_data).read()


def request_get(url):
    return urllib.urlopen(url).read()


def wrong_format(url='somewhere', reason='Unknown'):
    # TODO: email admin
    raise FormatError(url, reason)


def parse_select_item(soup):
    return [{"text": elem.text, "value": dict(elem.attrs)["value"]}
            for elem in soup.findAll("option")]


class GroupDataContainer(GroupData):

    def __init__(self, upper, lower):
        """Create GroupData with precomputed lists"""
        self.upper, self.lower = upper, lower

    def week(self, week_type):
        if week_type == UPPER_WEEK:
            return self.upper
        else:
            return self.lower
