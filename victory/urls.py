from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()



# Overriding the registration and making the form crispy

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field
from crispy_forms.bootstrap import FormActions
from registration_email.forms import EmailRegistrationForm
from django.conf import settings
from registration.backends import get_backend
from django.shortcuts import redirect
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.forms import CharField

from boogie.models import Player

# We don't do from registration.views import register
# But copy the code to add the saving of an extra field
def register(request, backend, success_url=None, form_class=None,
             disallowed_url='registration_disallowed',
             template_name='registration/registration_form.html',
             extra_context=None):
    backend = get_backend(backend)
    if not backend.registration_allowed(request):
        return redirect(disallowed_url)
    if form_class is None:
        form_class = backend.get_form_class(request)

    if request.method == 'POST':
        form = form_class(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_user = backend.register(request, **form.cleaned_data)

            # Custom code, creating player here ourselves
            player = Player.objects.create(user=new_user) # Default role is player
    
            import uuid
            player.emails_unsubscribe_hash = uuid.uuid4().hex
            player.pseudonym = form.cleaned_data.get('pseudonym')
            player.save()

            if success_url is None:
                to, args, kwargs = backend.post_registration_redirect(request, new_user)
                return redirect(to, *args, **kwargs)
            else:
                return redirect(success_url)
    else:
        form = form_class()
    
    if extra_context is None:
        extra_context = {}
    context = RequestContext(request)
    for key, value in extra_context.items():
        context[key] = callable(value) and value() or value

    return render_to_response(template_name,
                              {'form': form},
                              context_instance=context)

class CrispyRegistrationForm(EmailRegistrationForm):
    def __init__(self, *args, **kwargs):        
        super(CrispyRegistrationForm, self).__init__(*args, **kwargs)

        self.fields['pseudonym'] = CharField(label="Pennaam")

        self.helper = FormHelper()
        self.helper.form_class = 'form'
        self.helper.form_action = ''
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('email', css_class='input-block-level'),
            Field('pseudonym', css_class='input-block-level'),
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
