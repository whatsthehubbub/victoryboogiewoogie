from celery import task
from boogie.models import Player, Piece, Topic

from django.utils.timezone import utc
import datetime

import logging
logger = logging.getLogger('sake')

@task()
def get_new_assignment(player):
    return player.get_new_assignment()


@task()
def check_topic_pool():
    writer_topics = Topic.objects.filter(pool='WRITER').count()
    writers = Player.objects.filter(role="WRITER").count()

    difference = writers - writer_topics

    if difference > 0:
        # Promote topics to the writers pool
        player_topics = Topic.objects.filter(pool='PLAYER').order_by('-piece_count')[:difference]

        for topic in player_topics:
            topic.pool = 'WRITER'
            topic.save()

            logger.info("Promoted topic %s", unicode(topic))

        logger.info("Reset piece_count on all Topics to 0")
        Topic.objects.update(piece_count=0)


@task()
def pieces_assign():
    players_without = Player.objects.exclude(piece__status='ASSIGNED').exclude(piece__status='SUBMITTED').exclude(piece__status='NEEDSWORK')

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

    # Make sure all pieces have a datepublished
    for piece in Piece.objects.filter(datepublished=None):
        piece.datepublished = now
        piece.save()

        logger.info("Updated date published of piece %d", piece.id)

    for piece in Piece.objects.filter(status='ASSIGNED', deadline__lt=now):
        piece.status = "PASTDUE"
        piece.save()

        logger.info("Changed piece with id %d to PASTDUE", piece.id)

    for piece in Piece.objects.filter(status='NEEDSWORK', deadline__lt=now):
        piece.status = "PASTDUE"
        piece.save()

        logger.info("Changed piece with id %d to PASTDUE", piece.id)

    for piece in Piece.objects.filter(status='WAITING', datepublished__lt=now):
        piece.approve()

        logger.info("Waiting piece with id %d set to APPROVED.", piece.id)

@task()
def update_user_last_login(user):
    user.last_login = datetime.datetime.utcnow().replace(tzinfo=utc)
    user.save()

    logger.info("Updated last login time of user %s", user.username)

    return user
