from django.conf.urls import patterns, url

urlpatterns = patterns('',
    url(r'^$', 'boogie.views.index'),
    
    url(r'topics/$', 'boogie.views.topic_list'),
    url(r'topics/(\d+)/(\w+?)/', 'boogie.views.topic_detail'),

    url(r'pieces/$', 'boogie.views.piece_list'),
    url(r'pieces/(\d+)/$', 'boogie.views.piece_detail'),
    url(r'pieces/(\d+)/submit/', 'boogie.views.piece_submit', name='piece_submit'),
    url(r'pieces/queue/', 'boogie.views.piece_queue', name='piece_queue'),
)
