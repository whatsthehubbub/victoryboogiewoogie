# -*- coding: utf-8
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse

import datetime

from boogie.models import Player, Piece, Game

def player(request):
    returnDict = {}

    # TODO to remove the query per request, maybe it's better to store this in the request session
    
    if request.user.is_authenticated():
        try:
            returnDict['current_player'] = Player.objects.get(user=request.user)
        except ObjectDoesNotExist:
            returnDict['current_player'] = Player.objects.create(user=request.user, role="PLAYER")

        # TODO figure out a way to make this performant

        if returnDict['current_player'].role == 'PLAYER':
            if Piece.objects.filter(writer__user=request.user).filter(status='ASSIGNED'):
                returnDict['current_status'] = 'Bijdrage schrijven'
                returnDict['current_url'] = reverse('piece_submit')
            elif Piece.objects.filter(writer__user=request.user).filter(status='SUBMITTED'):
                returnDict['current_status'] = 'Bijdrage in behandeling…'
                returnDict['current_url'] = ''
            elif Piece.objects.filter(writer__user=request.user).filter(status='NEEDSWORK'):
                returnDict['current_status'] = 'Bijdrage verbeteren'
                returnDict['current_url'] = reverse('piece_submit')
            else:
                returnDict['current_status'] = 'Wachten op opdracht…'
                returnDict['current_url'] = ''
        else: # Writers can always write something
            returnDict['current_status'] = 'Bijdrage schrijven'
            returnDict['current_url'] = reverse('piece_submit')

    try:
        startDate = Game.objects.get_latest_game().start_date
        today = datetime.date.today()

        delta = today - startDate

        if today >= startDate:
            returnDict['gameWeek'] = (delta.days / 7) + 1
        else:
            returnDict['gameWeek'] = 0
    except IndexError:
        pass

    return returnDict
