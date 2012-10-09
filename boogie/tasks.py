from celery import task

@task()
def add(x, y):
	return x+y


@task()
def get_new_assignment(player):
	# TODO make another function to sweep everybody and give them new tasks
	player.get_new_assignment()


@task()
def check_topic_pool(topic):
	topic.check_pool()