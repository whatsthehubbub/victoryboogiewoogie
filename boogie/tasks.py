from celery import task

@task()
def get_new_assignment(player):
    # TODO make another function to sweep everybody and give them new tasks
    return player.get_new_assignment()


@task()
def check_topic_pool(topic):
    return topic.check_pool()
