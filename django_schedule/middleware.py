from django import http
from django.conf import settings
from google.appengine._internal.django.utils.http import urlquote

class DomainRedirectMiddleware(object):

    def process_request(self, request):
        redirect_map = getattr(settings, 'DOMAIN_REDIRECT_MAP', None)
        if not redirect_map:
            return

        if request.get_host() in redirect_map:
            new_url = "%s://%s%s" % (
                request.is_secure() and "https" or "http",
                redirect_map[request.get_host()],
                request.get_full_path())

            return http.HttpResponsePermanentRedirect(new_url)
