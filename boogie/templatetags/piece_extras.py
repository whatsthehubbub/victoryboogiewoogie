from django import template

from boogie.models import PieceVote

register = template.Library()

def likes(player, piece):
    try:
        PieceVote.objects.get(player=player, piece=piece)
        return True
    except:
        return False

register.filter('likes', likes)
