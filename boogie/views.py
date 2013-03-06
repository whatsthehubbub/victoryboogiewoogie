from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.template import RequestContext, loader
from django.forms import ModelForm, ChoiceField, ModelChoiceField, ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Q

from django.contrib.auth.decorators import login_required, user_passes_test

from boogie.models import *

from boogie import tasks

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, Field, HTML
from crispy_forms.bootstrap import FormActions


def index(request):
    t = loader.get_template('boogie/index.html')
    
    c = RequestContext(request, {
            'frontpage_pieces': Piece.objects.exclude(frontpage=False).filter(status='APPROVED').order_by('-datepublished')[:5],
            'summary': Summary.objects.all().order_by('-datecreated'),
            'characters': Character.objects.all()
    })

    return HttpResponse(t.render(c))


class PreLaunchEmailForm(ModelForm):
    class Meta:
        model = PreLaunchEmail
        fields = ('email', )

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = 'form'
        self.helper.form_action = ''
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('email', css_class='input-block-level', placeholder='email@adres.nl'),
            FormActions(
                Submit('submit', 'Verzenden', css_class='btn')
            )
        )

        super(PreLaunchEmailForm, self).__init__(*args, **kwargs)

def colofon(request):
    t = loader.get_template('boogie/colofon.html')
    
    c = RequestContext(request, {
        'writers': Player.objects.filter(role='WRITER')
    })

    return HttpResponse(t.render(c))

def pre_launch(request):
    t = loader.get_template('boogie/pre_launch.html')
    
    if request.method == 'POST':
        form = PreLaunchEmailForm(request.POST)

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('pre_launch_thanks'))
    else:
        form = PreLaunchEmailForm()

    c = RequestContext(request, {
        'form': form
    })
    return HttpResponse(t.render(c))

def summary(request):
    t = loader.get_template('boogie/summary.html')

    c = RequestContext(request, {
        'summary': Summary.objects.all().order_by('-datecreated')
    })

    return HttpResponse(t.render(c))

def notifications(request):
    player = Player.objects.get(user=request.user)

    tasks.update_user_last_login.apply_async(args=[request.user], countdown=10)

    t = loader.get_template('boogie/notifications.html')

    c = RequestContext(request, {
        'notifications': Notification.objects.filter(for_player=player).order_by('-datecreated')
    })

    return HttpResponse(t.render(c))
    
def topic_list(request):
    t = loader.get_template('boogie/topic_list.html')
    
    c = RequestContext(request, {
            'writer_topics': Topic.objects.exclude(archived=True).filter(pool='WRITER').order_by('title'),
            'player_topics': Topic.objects.exclude(archived=True).filter(pool='PLAYER').order_by('title'),
            'archived_topics': Topic.objects.filter(archived=True).order_by('title')
    })
    return HttpResponse(t.render(c))
    
def topic_detail(request, topicid, slug):
    t = loader.get_template('boogie/topic_detail.html')
    
    order = request.GET.get('order', '-score_cache')

    topic = Topic.objects.get(id=topicid)

    c = RequestContext(request, {
            'topic': topic,
            'pieces': topic.approved_pieces().order_by(order),
            'order': order
    })
    return HttpResponse(t.render(c))
    
def piece_list(request):
    t = loader.get_template('boogie/piece_list.html')
    
    c = RequestContext(request, {
            'pieces': Piece.objects.filter(status='APPROVED').order_by('-score_cache')
    })
    return HttpResponse(t.render(c))

def pieces_per_week(request, week):
    week = int(week)
    datestart = Game.objects.get_latest_game().start_date

    weekStart = datestart + datetime.timedelta((week-1) * 7)
    weekEnd = datestart + datetime.timedelta((week) * 7)

    order_crit = request.GET.get('order', '-score_cache')

    t = loader.get_template('boogie/pieces_per_week.html')

    c = RequestContext(request, {
        'pieces': Piece.objects.filter(datepublished__gte=weekStart).filter(datepublished__lte=weekEnd).order_by(order_crit),
        'week': week,
        'order': order_crit
    })

    return HttpResponse(t.render(c))

def piece_detail(request, id):
    piece = Piece.objects.get(id=id)

    show = False

    if piece.status == 'APPROVED':
        show = True
    elif request.user.is_authenticated:
        if request.user.is_superuser:
            show = True
        else:
            player = Player.objects.get(user=request.user)

            if player.role == 'WRITER' or player==piece.writer:
                show = True

    if show:
        t = loader.get_template('boogie/piece_detail.html')

        c = RequestContext(request, {
            'piece': piece
        })
        return HttpResponse(t.render(c))
    else:
        return HttpResponseRedirect(reverse('index'))
        
class PieceSubmitForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(PieceSubmitForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = 'form'
        self.helper.form_action = ''
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('genre', css_class='input-block-level'),
            Field('title', css_class='input-block-level'),
            Field('text', css_class='input-block-level'),
            HTML('<p id="charactercount" class="pull-right label">5000</p>'),
            Field('new_topic', css_class="input-block-level"),
            FormActions(
                Submit('submit', 'Opslaan', css_class='btn')
            )
        )

    genre = ChoiceField(choices=PIECE_GENRE_CHOICES[:-1])

    class Meta:
        model = Piece
        fields = ('genre', 'title', 'text', 'new_topic')

    def clean_title(self):
        title = self.cleaned_data.get('title')

        if not title:
            raise ValidationError("Je hebt geen titel ingevuld.")

        return title

    def clean_new_topic(self):
        new_topic = self.cleaned_data.get('new_topic')

        if not new_topic:
            raise ValidationError("Je hebt geen nieuw onderwerp ingevuld.")

        try:
            Topic.objects.get(title=new_topic)
            raise ValidationError("Dit onderwerp bestaat al. Verzin iets anders.")
        except Topic.DoesNotExist:
            pass

        return new_topic

    def clean(self):
        cleaned_data = super(PieceSubmitForm, self).clean()

        text = cleaned_data.get('text')
        genre = cleaned_data.get('genre')

        if not text and (genre != 'Headline' and genre != 'Illustratie'):
            raise ValidationError("Schrijf een tekst of kies headline als genre.")

        return cleaned_data

@login_required
def piece_submit(request):
    t = loader.get_template('boogie/piece_submit.html')
    
    player = Player.objects.get(user=request.user)
    form = None

    if player.role == 'PLAYER':
        assignments = Piece.objects.filter(Q(status='ASSIGNED') | Q(status='NEEDSWORK')).filter(writer__user=request.user)
        if assignments:
            # If we have more than one assignment, we just get the first
            piece = assignments[0]

            if request.method == 'POST':
                form = PieceSubmitForm(request.POST, instance=piece)
                if form.is_valid():
                    # The piece has been submitted into the bowels of the system
                    form.instance.status = 'SUBMITTED'
                    form.save()

                    return HttpResponseRedirect(reverse('piece_submit_thanks'))
            else:
                form = PieceSubmitForm(instance=piece)
    
    c = RequestContext(request, {
            'form': form
    })
    return HttpResponse(t.render(c))


class WriterPieceSubmitForm(ModelForm):
    topic = ModelChoiceField(queryset=Topic.objects.exclude(archived=True).filter(pool='WRITER'), label='Onderwerp')

    class Meta:
        model = Piece
        fields = ('topic', 'character', 'image', 'genre', 'title', 'text')

    def clean_genre(self):
        genre = self.cleaned_data['genre']

        if not genre:
            raise ValidationError("Je hebt geen genre ingevuld.")

        return genre

    def clean_title(self):
        title = self.cleaned_data['title']

        if not title:
            raise ValidationError("Je hebt geen titel ingevuld.")

        return title

    def clean(self):
        cleaned_data = super(WriterPieceSubmitForm, self).clean()

        text = cleaned_data.get('text')
        genre = cleaned_data.get('genre')

        if not text and (genre != 'Headline' and genre != 'Illustratie'):
            raise ValidationError("Schrijf een tekst (voor niet headline / illustratie bijdragen).")

        return cleaned_data

@login_required
def writer_piece_submit(request):
    t = loader.get_template('boogie/writer_piece_submit.html')

    player = Player.objects.get(user=request.user)

    if player.role == 'WRITER':
        if request.method == 'POST':
            form = WriterPieceSubmitForm(request.POST, request.FILES)
            
            # TODO check for compulsory fields

            if form.is_valid():
                piece = form.save(commit=False)

                piece.status = 'APPROVED'
                piece.datepublished = datetime.datetime.utcnow().replace(tzinfo=utc)
                piece.writer = player
                piece.deadline = datetime.datetime.utcnow().replace(tzinfo=utc)

                piece.save()

                topic = piece.topic
                topic.pool = 'PLAYER'
                topic.save()

                return HttpResponseRedirect(reverse('piece_detail', args=[piece.id]))

        else:
            form = WriterPieceSubmitForm()

        c = RequestContext(request, {
            'form': form
        })

        return HttpResponse(t.render(c))
    else:
        return HttpResponseRedirect(reverse('piece_submit'))

@require_POST
@login_required
def piece_validate(request, piece_id):
    player = Player.objects.get(user=request.user)

    if player.role == 'WRITER':
        piece = Piece.objects.get(id=piece_id)
    
        valid = request.POST.get('ok', '')

        if valid == 'yes':
            piece.approve() # Saves internally

        elif valid == 'retry':
            # The piece needs more work
            piece.rejection_reason = request.POST.get('reason', '')
            piece.status = 'NEEDSWORK'

            Notification.objects.create_new_needswork_notification(piece.writer, piece)
        elif valid == 'no':
            piece.status = 'REJECTED'

            Notification.objects.create_new_rejected_notification(piece.writer, piece)

        piece.save()
            
        return HttpResponseRedirect(reverse('piece_queue'))

@user_passes_test(lambda u: u.is_superuser)
def pieces_assign(request):
    counter = tasks.pieces_assign()

    return HttpResponse('Spelers met een nieuwe opdracht: %d' % counter)

@login_required
@require_POST
def piece_vote_up(request, piece_id):
    piece = Piece.objects.get(id=piece_id)

    player = Player.objects.get(user=request.user)

    piece.vote_up(player)
    piece.update_score_cache()

    return_url = request.POST.get('return_url', '')
    if return_url:
        return HttpResponseRedirect(return_url)
    else:
        return HttpResponseRedirect(reverse('boogie.views.piece_detail', args=[piece.id]))

@login_required
@require_POST
def piece_vote_up_undo(request, piece_id):
    piece = Piece.objects.get(id=piece_id)
    player = Player.objects.get(user=request.user)

    piece.vote_up_undo(player)
    piece.update_score_cache()

    return_url = request.POST.get('return_url', '')
    if return_url:
        return HttpResponseRedirect(return_url)
    else:
        return HttpResponseRedirect(reverse('boogie.views.piece_detail', args=[piece.id]))

@login_required    
def piece_queue(request):
    player = Player.objects.get(user=request.user)

    if player.role == 'WRITER':    
        t = loader.get_template('boogie/piece_queue.html')

        c = RequestContext(request, {
            'pieces': Piece.objects.filter(status='SUBMITTED').order_by('-datecreated')
        })
        return HttpResponse(t.render(c))

def player_profile(request, name):
    player = Player.objects.get(user__username=name)

    c = RequestContext(request, {
        'player': player
    })
    
    t = loader.get_template('boogie/player_profile.html')

    # Show the approved pieces in any case
    c['approved_pieces'] = player.pieces().filter(status="APPROVED")

    if request.user.username == name:
        c['assigned_pieces'] = player.pieces().filter(status="ASSIGNED")
        c['submitted_pieces'] = player.pieces().filter(status="SUBMITTED")

        c['needswork_pieces'] = player.pieces().filter(status="NEEDSWORK")
        c['rejected_pieces'] = player.pieces().filter(status="REJECTED")
    
    return HttpResponse(t.render(c))


class PlayerProfileForm(ModelForm):
    class Meta:
        model = Player
        fields = ('pseudonym', 'onelinebio', 'send_emails')

    def __init__(self, *args, **kwargs):
        self.helper = FormHelper()
        self.helper.form_class = 'form'
        self.helper.form_action = ''
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Div(
                Field('pseudonym', css_class='input-block-level'),
                Field('onelinebio', css_class='input-block-level'),
                Field('send_emails', css_class='')
            ),
            FormActions(
                Submit('submit', 'Opslaan', css_class='btn')
            )
        )

        super(PlayerProfileForm, self).__init__(*args, **kwargs)

    def clean_pseudonym(self):
        pseudonym = self.cleaned_data['pseudonym']

        if not pseudonym:
            raise ValidationError("Vul een pennaam in.")

        return pseudonym

@login_required
def player_profile_edit(request, name):
    t = loader.get_template('boogie/player_profile_edit.html')

    player = Player.objects.get(user__username=name)
    if request.user == player.user:
        if request.method == 'POST':
            playerform = PlayerProfileForm(request.POST, request.FILES, instance=player)

            if playerform.is_valid():
                playerform.save()

                return HttpResponseRedirect(reverse('boogie.views.player_profile', args=[name]))
        else:
            playerform = PlayerProfileForm(instance=player)

        c = RequestContext(request, {
            'playerform': playerform
        })

        return HttpResponse(t.render(c))

def player_unsubscribe(request, h):
    try:
        player = Player.objects.get(emails_unsubscribe_hash=h)
        player.send_emails = False
        player.update_unsubscribe_hash()
        player.save()
    except:
        logging.error("Tried to unsubscribe player with hash %s", h)

    return HttpResponseRedirect(reverse('index'))

def character_profile(request, id):
    character = Character.objects.get(id=id)

    order = request.GET.get('order', '-datecreated')

    t = loader.get_template('boogie/character_profile.html')

    c = RequestContext(request, {
        'character': character,
        'order': order,
        'pieces': Piece.objects.filter(status='APPROVED', character=character).order_by(order)
    })

    return HttpResponse(t.render(c))
