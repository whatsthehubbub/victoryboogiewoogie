from celery import task
from boogie.models import Player

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

# class PeriodicAssignment(PeriodicTask):
#     def run(self, **kwargs):
#         logger.info("Running PeriodicAssignment")

#     def is_due(self, last_run_at):
#         return (True, 60)
