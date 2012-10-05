from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'boogie.views.index', name='index'),
    
    url(r'topics/$', 'boogie.views.topic_list', name='topic_list'),
    url(r'topics/(\d+)/(\w+?)/', 'boogie.views.topic_detail', name="topic_detail"),

    url(r'pieces/$', 'boogie.views.piece_list'),
    url(r'pieces/queue/', 'boogie.views.piece_queue', name='piece_queue'),
    
    url(r'pieces/(\d+)/$', 'boogie.views.piece_detail'),
    url(r'pieces/(\d+)/submit/', 'boogie.views.piece_submit', name='piece_submit'),
    url(r'pieces/(\d+)/validate/', 'boogie.views.piece_validate', name='piece_validate'),
    url(r'pieces/(\d+)/vote/up/', 'boogie.views.piece_vote_up', name='piece_vote_up'),

    url(r'writers/(\w+?)/$', 'boogie.views.writer_profile', name='writer_profile'),
)
