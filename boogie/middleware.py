from django.http import HttpResponsePermanentRedirect

class WWWRedirectMiddleware(object):
    def process_request(self, request):
        # Check that we're not on the dev server
        # And check if there isn't www in front of the URL
        if not request.META['HTTP_HOST'].startswith('127.') and not request.META['HTTP_HOST'].startswith('wwww.'):
            return HttpResponsePermanentRedirect('http://www.gidsgame.nl')

from boogie.models import Game
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.conf import settings

class PreLaunchMiddleware(object):
    def process_request(self, request):
        game = Game.objects.get_latest_game()

        if request.path.startswith(settings.STATIC_URL) or request.path.startswith('/admin') or request.path.startswith(reverse('boogie.views.pre_launch')):
            return None

        if not game.started:
            return HttpResponseRedirect(reverse('boogie.views.pre_launch'))
