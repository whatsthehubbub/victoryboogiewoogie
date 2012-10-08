from django.core.exceptions import ObjectDoesNotExist

from boogie.models import Player

def player(request):
    returnDict = {}

    # TODO to remove the query per request, maybe it's better to store this in the request session
    try:
        returnDict['player'] = Player.objects.get(user=request.user)
    except ObjectDoesNotExist:
        pass

    return returnDict
