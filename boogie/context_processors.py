# -*- coding: utf-8
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings

import datetime

from boogie.models import Player, Piece

def player(request):
    returnDict = {}

    # TODO to remove the query per request, maybe it's better to store this in the request session
    
    if request.user.is_authenticated():
        try:
            returnDict['current_player'] = Player.objects.get(user=request.user)
        except ObjectDoesNotExist:
            pass

        # TODO figure out a way to make this performant
        if Piece.objects.filter(writer__user=request.user).filter(status='ASSIGNED'):
            returnDict['current_status'] = 'Bijdrage schrijven'
        elif Piece.objects.filter(writer__user=request.user).filter(status='SUBMITTED'):
            returnDict['current_status'] = 'Bijdrage in behandeling…'
        elif Piece.objects.filter(writer__user=request.user).filter(status='NEEDSWORK'):
            returnDict['current_status'] = 'Bijdrage verbeteren'
        else:
            returnDict['current_status'] = 'Wachten op opdracht…'

    # TODO figure out when the game starts
    startDate = settings.GAME_START
    delta = datetime.date.today() - startDate

    returnDict['gameWeek'] = delta.days / 7

    return returnDict
