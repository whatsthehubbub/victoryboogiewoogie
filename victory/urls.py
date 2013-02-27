from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()



# Overriding the registration and making the form crispy

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field
from crispy_forms.bootstrap import FormActions
from registration_email.forms import EmailRegistrationForm
from registration.views import register
from django.conf import settings

class CrispyRegistrationForm(EmailRegistrationForm):
    def __init__(self, *args, **kwargs):        
        super(CrispyRegistrationForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = 'form'
        self.helper.form_action = ''
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('email', css_class='input-block-level'),
            Field('password1', css_class='input-block-level'),
            Field('password2', css_class='input-block-level'),
            FormActions(
                Submit('submit', 'Aanmelden', css_class='btn')
            )
        )

urlpatterns = patterns('',
    # Examples:
    url(r'^', include('boogie.urls')),

    # Override the register URL to pass in our crispy form
    url(r'^register/$',
        register,
        {'backend': 'registration.backends.default.DefaultBackend',
         'template_name': 'registration/registration_form.html',
         'form_class': CrispyRegistrationForm,
         'success_url': getattr(
             settings, 'REGISTRATION_EMAIL_REGISTER_SUCCESS_URL', None),
        },
        name='registration_register',
    ),
    url(r'^', include('registration_email.backends.default.urls')),


    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)


from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns += staticfiles_urlpatterns()
