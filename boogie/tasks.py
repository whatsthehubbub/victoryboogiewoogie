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
        # Move topics to the writers pool
        # TODO doing this in pure python right now

        annotated_list = []

        player_topics = Topic.objects.filter(pool='PLAYER')
        for topic in player_topics:
            annotated_list.append((topic, topic.approved_pieces_since()))

        annotated_list.sort(key=lambda topic: topic[1])

        to_promote = annotated_list[:difference]
        for topic in to_promote:
            logger.info("Promoting topic %s", str(topic))
            topic.update(pool='WRITER')



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

    for piece in Piece.objects.filter(status='ASSIGNED', deadline__lt=now):
        piece.status = "PASTDUE"
        piece.save()

        logger.info("Changed piece with id %d to PASTDUE", piece.id)

    for piece in Piece.objects.filter(status='NEEDSWORK', deadline__lt=now):
        piece.status = "PASTDUE"
        piece.save()

        logger.info("Changed piece with id %d to PASTDUE", piece.id)

    for piece in Piece.objects.filter(status='WAITING', datepublished__lt=now):
        piece.status = 'APPROVED'
        piece.save()

        logger.info("Waiting piece with id %d set to APPROVED.", piece.id)

@task()
def update_user_last_login(user):
    user.last_login = datetime.datetime.utcnow().replace(tzinfo=utc)
    user.save()

    logger.info("Updated last login time of user %s", str(user))

    return user