from django import template

from boogie.models import PieceVote, Notification

register = template.Library()

@register.filter
def likes(player, piece):
    try:
        PieceVote.objects.get(player=player, piece=piece)
        return True
    except:
        return False


@register.filter
def new_notifications(player):
    return Notification.objects.new_notifications_for_player(player)


@register.filter
def counterzerocomma(counter0, list):
    if counter0 < len(list)-2:
        return True
    else:
        return False

@register.filter
def counterzeroand(counter0, list):
    if counter0 < len(list-1):
        return True
    else:
        return False