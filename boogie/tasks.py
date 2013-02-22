from celery import task
from boogie.models import Player, Piece

from django.utils.timezone import utc
import datetime

import logging
logger = logging.getLogger('sake')

@task()
def get_new_assignment(player):
    return player.get_new_assignment()


@task()
def check_topic_pool(topic):
    return topic.check_pool()



@task()
def pieces_assign():
    players_without = Player.objects.exclude(piece__status='ASSIGNED').exclude(piece__status='NEEDSWORK')

    counter = 0
    for player in players_without:
        player.get_new_assignment()
        counter += 1

    logger.info('Assigned %d players a new piece', counter)

    return counter

@task()
def piece_cleanup():
    # Pieces whose deadline has passed, will be set to PASTDUE

    now = datetime.datetime.utcnow().replace(tzinfo=utc)

    for piece in Piece.objects.filter(status='ASSIGNED', deadline__lt=now):
        piece.status = "PASTDUE"
        piece.save()

    for piece in Piece.objects.filter(status='NEEDSWORK', deadline__lt=now):
        piece.status = "PASTDUE"
        piece.save()


    # Pieces that need to be published will be published
    # TODO

@task()
def update_user_last_login(user):
    user.last_login = datetime.datetime.utcnow().replace(tzinfo=utc)
    user.save()

    logger.info("Updated last login time of user %s", str(user))

    return user
