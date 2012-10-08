from django.core.exceptions import ObjectDoesNotExist

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

    startDate = datetime.date(2012, 9, 20)
    delta = datetime.date.today() - startDate

    returnDict['week'] = delta.days / 7

    return returnDict
