from django.http import HttpResponsePermanentRedirect

class WWWRedirectMiddleware(object):
    def process_request(self, request):
        # Check that we're not on the dev server
        # And check if there isn't www in front of the URL
        if not request.META['HTTP_HOST'].startswith('127.') and not request.META['HTTP_HOST'].startswith('wwww.'):
            return HttpResponsePermanentRedirect('http://www.gidsgame.nl')
