from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

import datetime

from boogie.models import Player

def player(request):
    returnDict = {}

    # TODO to remove the query per request, maybe it's better to store this in the request session
    
    if request.user.is_authenticated():
        try:
            returnDict['current_player'] = Player.objects.get(user=request.user)
        except ObjectDoesNotExist:
            pass

    # TODO figure out when the game starts
    startDate = settings.GAME_START
    delta = datetime.date.today() - startDate

    returnDict['gameWeek'] = delta.days / 7

    return returnDict
