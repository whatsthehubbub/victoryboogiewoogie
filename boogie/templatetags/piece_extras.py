from django import template

from boogie.models import PieceVote

register = template.Library()

def likes(player, piece):
	return PieceVote.vote_exists(player, piece)

register.filter('likes', likes)