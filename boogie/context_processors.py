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
                returnDict['current_explanation'] = ''
            elif Piece.objects.filter(writer__user=request.user).filter(status='SUBMITTED'):
                returnDict['current_status'] = 'Bijdrage in behandeling…'
                returnDict['current_url'] = ''
                returnDict['current_explanation'] = 'De redactie buigt zich momenteel over je ingestuurde bijdrage. Je ontvangt bericht zodra je bijdrage is goedgekeurd of geredigeerd. Een moment geduld a.u.b.'
            elif Piece.objects.filter(writer__user=request.user).filter(status='NEEDSWORK'):
                returnDict['current_status'] = 'Bijdrage verbeteren'
                returnDict['current_url'] = reverse('piece_submit')
                returnDict['current_explanation'] = ''
            else:
                returnDict['current_status'] = 'Wachten op opdracht…'
                returnDict['current_url'] = ''
                returnDict['current_explanation'] = 'Je ontvangt spoedig een nieuwe schrijfopdracht. Zodra dit gebeurt sturen we je een bericht.'
        else: # Writers can always write something
            returnDict['current_status'] = 'Bijdrage schrijven'
            returnDict['current_url'] = reverse('writer_piece_submit')
            returnDict['current_explanation'] = ''

    try:
        game = Game.objects.get_latest_game()
        returnDict['game'] = game
    except:
        pass

    return returnDict
