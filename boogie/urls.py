from django.conf.urls import patterns, url


from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field
from crispy_forms.bootstrap import FormActions
from django.contrib.auth.forms import PasswordResetForm

class CrispyResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):        
        super(CrispyResetForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = 'form'
        self.helper.form_action = 'auth_password_reset'
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('email', css_class='input-block-level'),
            FormActions(
                Submit('submit', 'Verzenden', css_class='btn')
            )
        )


urlpatterns = patterns('',
    url(r'^$', 'boogie.views.index', name='index'),

    url(r'^colofon/$', 'boogie.views.colofon', name='colofon'),
    url(r'^help/$', 'django.views.generic.simple.direct_to_template', {'template': 'boogie/help.html'}, name='help'),

    url(r'^pre/launch/$', 'boogie.views.pre_launch', name='pre_launch'),
    url(r'^pre/launch/thanks/$', 'django.views.generic.simple.direct_to_template', {'template': 'boogie/pre_launch_thanks.html'}, name='pre_launch_thanks'),
    
    # TODO these are redefined in the included registration URL
    url(r'^login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^logout/$', 'django.contrib.auth.views.logout_then_login', name='logout'),
    url(r'^password/reset/$', 'django.contrib.auth.views.password_reset', {'password_reset_form': CrispyResetForm}, name='password_reset'),
    url(r'^password/reset/done/$', 'django.contrib.auth.views.password_reset_done', name='password_reset_done'),
    url(r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)/(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm', name='password_reset_confirm'),
    url(r'^password/reset/complete/$', 'django.contrib.auth.views.password_reset_complete', name='password_reset_complete'),

    url(r'^spelregels/$', 'django.views.generic.simple.direct_to_template', {'template': 'boogie/editors.html'}, name='editors'),
    url(r'^samenvatting/$', 'boogie.views.summary', name='summary'),
    url(r'^berichten/$', 'boogie.views.notifications', name='notifications'),

    url(r'^onderwerpen/$', 'boogie.views.topic_list', name='topic_list'),
    url(r'^onderwerpen/(\d+)/(\S+?)/$', 'boogie.views.topic_detail', name="topic_detail"),

    url(r'^bijdragen/$', 'boogie.views.piece_list', name='pieces_list'),
    url(r'^bijdragen/week/(\d+)/$', 'boogie.views.pieces_per_week', name='pieces_per_week'),
    url(r'^bijdragen/queue/', 'boogie.views.piece_queue', name='piece_queue'),
    
    url(r'^bijdragen/(\d+)/$', 'boogie.views.piece_detail', name='piece_detail'),

    url(r'^bijdragen/schrijven/schrijver/$', 'boogie.views.writer_piece_submit', name='writer_piece_submit'),
    url(r'^bijdragen/schrijven/$', 'boogie.views.piece_submit', name='piece_submit'),
    url(r'^bijdragen/schrijven/bedankt/$', 'django.views.generic.simple.direct_to_template', {'template': 'boogie/piece_submit_thanks.html'}, name='piece_submit_thanks'),
    
    url(r'^bijdragen/toekennen/$', 'boogie.views.pieces_assign', name='pieces_assign'),
    
    url(r'^bijdragen/(\d+)/validate/$', 'boogie.views.piece_validate', name='piece_validate'),
    url(r'^bijdragen/(\d+)/vote/up/$', 'boogie.views.piece_vote_up', name='piece_vote_up'),
    url(r'^bijdragen/(\d+)/vote/up/undo/$', 'boogie.views.piece_vote_up_undo', name='piece_vote_up_undo'),

    url(r'^users/(?P<name>\w+?)/$', 'django.views.generic.simple.redirect_to', {'url': '/spelers/%(name)s/'}),

    url(r'^personages/(\d+?)/$', 'boogie.views.character_profile', name='character_profile'),

    url(r'^spelers/(\w+?)/$', 'boogie.views.player_profile', name='player_profile'),
    url(r'^spelers/(\w+?)/edit/$', 'boogie.views.player_profile_edit', name='player_profile_edit'),
    url(r'^spelers/(\S+?)/unsubscribe/$', 'boogie.views.player_unsubscribe', name='player_unsubscribe'),
)
