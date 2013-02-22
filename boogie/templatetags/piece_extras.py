from django import template

from boogie.models import PieceVote, Notification

register = template.Library()

def likes(player, piece):
    try:
        PieceVote.objects.get(player=player, piece=piece)
        return True
    except:
        return False

register.filter('likes', likes)


def new_notifications(player):
    return Notification.objects.new_notifications_for_player(player)

register.filter('new_notifications', new_notifications)
