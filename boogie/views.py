from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.template import RequestContext, loader
from django.forms import ModelForm, ChoiceField, ModelChoiceField, ValidationError
from django.core.urlresolvers import reverse
from django.db.models import Q

from django.contrib.auth.decorators import login_required, user_passes_test

from django.shortcuts import render_to_response

from boogie.models import *

from boogie import tasks

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Div, Field, HTML
from crispy_forms.bootstrap import FormActions


import bleach
from boogie.bleach_common import BLEACH_TAGS, BLEACH_ATTRIBUTES


def index(request):
    t = loader.get_template('boogie/index.html')
    
    frontpage_pieces = Piece.objects.exclude(frontpage=False).filter(status='APPROVED').order_by('-datepublished')
    ads = Advertisement.objects.filter(active=True).order_by('rank')

    max_ad_rank = Advertisement.objects.filter(active=True).aggregate(Max('rank'))['rank__max']
    max_items = frontpage_pieces.count() + ads.count()

    piece_and_ads = (max(max_ad_rank, max_items)+2) * [None]

    for ad in ads:
        piece_and_ads[ad.rank] = ('ad', ad)

    piece_counter = 0

    for counter in range(1, len(piece_and_ads)):
        if not piece_and_ads[counter]:
            try:
                piece_and_ads[counter] = ('piece', frontpage_pieces[piece_counter])
            except IndexError:
                pass # Ran out of pieces
            
            piece_counter += 1

    piece_and_ads = [el for el in piece_and_ads if el]

    c = RequestContext(request, {
            'piece_and_ads': piece_and_ads,
            'summary': Summary.objects.all().order_by('-datecreated'),
            'characters': Character.objects.all().order_by('order', 'name')
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
    
    game = Game.objects.get_latest_game()

    if game.started:
        return HttpResponseRedirect(reverse('index'))
    else:
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
        'summary': Summary.objects.all().order_by('datecreated')
    })

    return HttpResponse(t.render(c))

@login_required
def notifications(request):
    t = loader.get_template('boogie/notifications.html')

    try:
        player = Player.objects.get(user=request.user)

        tasks.update_user_last_login.apply_async(args=[request.user], countdown=10)

        notifications = Notification.objects.filter(for_player=player).order_by('-datecreated')
    except Player.DoesNotExist:
        notifications = []


    c = RequestContext(request, {
        'notifications': notifications
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
    
    order = request.GET.get('order', '-datepublished')

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

    # TODO not good to pass dates into a datetime compare, but it works
    weekStart = datestart + datetime.timedelta((week-1) * 7)
    
    if week == 1:
        # For the first week shift the lower bound to include everything up until then
        weekStart -= datetime.timedelta(days=500)

    weekEnd = datestart + datetime.timedelta((week) * 7)

    order_crit = request.GET.get('order', '-datepublished')

    t = loader.get_template('boogie/pieces_per_week.html')

    c = RequestContext(request, {
        'pieces': Piece.objects.filter(status="APPROVED").filter(datepublished__gte=weekStart).filter(datepublished__lte=weekEnd).order_by(order_crit),
        'week': week,
        'order': order_crit
    })

    return HttpResponse(t.render(c))

def piece_detail(request, id):
    piece = Piece.objects.get(id=id)

    show = False

    if piece.status == 'APPROVED':
        show = True
    elif request.user.is_authenticated():
        if request.user.is_superuser:
            show = True
        else:
            player = Player.objects.get(user=request.user)

            if player.role == 'WRITER' or player==piece.writer:
                show = True

    if show:
        t = loader.get_template('boogie/piece_detail.html')

        try:
            fallback = Character.objects.all()[0].avatar.url
        except:
            fallback = ''

        c = RequestContext(request, {
            'piece': piece,
            'fallback_image': fallback
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
            HTML('<span class="help-block">Dit onderwerp wordt toegevoegd aan de spelerslijst nadat je bijdrage is goedgekeurd. Gebruik het om het verhaal te be&iuml;nvloeden. Hint: kies een element uit je bijdrage als nieuw onderwerp.</span>'),
            FormActions(
                Submit('submit', 'Voorbeeld tonen', css_class='btn'),
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

    def clean_text(self):
        text = self.cleaned_data.get('text')

        text = bleach.clean(text, tags=[], strip=True)

        return text


    def clean_new_topic(self):
        new_topic = self.cleaned_data.get('new_topic')

        if not new_topic:
            raise ValidationError("Je hebt geen nieuw onderwerp ingevuld.")

        try:
            Topic.objects.get(title__iexact=new_topic)
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
    player = Player.objects.get(user=request.user)

    if player.role == 'PLAYER':
        assignments = Piece.objects.filter(Q(status='ASSIGNED') | Q(status='NEEDSWORK')).filter(writer__user=request.user)

        if assignments:
            # If we have more than one assignment (which should not happen), we just get the first
            piece = assignments[0]

            form = PieceSubmitForm(instance=piece)

            if request.method == 'POST':
                # We get data submitted
                save = request.POST.get('save', '') == 'save'
                edit = request.POST.get('save', '') == 'edit'

                form = PieceSubmitForm(request.POST, instance=piece)

                if not (edit or save) and not form.is_valid():
                    pass # Go back to the edit page
                elif edit:
                    form = PieceSubmitForm(instance=piece)
                elif save:
                    piece.status = 'SUBMITTED'
                    piece.save()

                    return HttpResponseRedirect(reverse('piece_submit_thanks'))
                elif form.is_valid():
                    piece = form.save()

                    return render_to_response('boogie/piece_submit_preview.html', {
                        'piece': piece
                    }, RequestContext(request))
        else:
            form = None

        return render_to_response('boogie/piece_submit.html', {
                'form': form
        }, RequestContext(request))


class WriterPieceSubmitForm(ModelForm):
    topic = ModelChoiceField(queryset=Topic.objects.exclude(archived=True).filter(pool='WRITER'), label='Onderwerp')

    class Meta:
        model = Piece
        fields = ('topic', 'character', 'image', 'genre', 'title', 'text')

    def __init__(self, *args, **kwargs):
        super(WriterPieceSubmitForm, self).__init__(*args, **kwargs)

        self.helper = FormHelper()
        self.helper.form_class = 'form'
        self.helper.form_action = ''
        self.helper.form_method = 'post'

        self.helper.layout = Layout(
            Field('topic', css_class='input-block-level'),
            HTML('<span class="help-block">Hint: lees de laatste speler-bijdrage over dit onderwerp en verwerk het in je bijdrage.</span>'),
            Field('character', css_class='input-block-level'),
            Field('genre', css_class="input-block-level"),
            Field('title', css_class="input-block-level"),
            Field('text', css_class="input-block-level"),
            HTML('<input type="hidden" name="pieceid" value="{{ form.instance.pk|default_if_none:"" }}">'),
            HTML('<p id="charactercount" class="pull-right label">5000</p>'),
            HTML('<span class="help-block">De volgende HTML is toegestaan: <br>&lt;a href="" title=""&gt; &lt;abbr title=""&gt; &lt;acronym title=""&gt; &lt;b&gt; &lt;blockquote cite=""&gt; &lt;cite&gt; &lt;code&gt; &lt;del datetime=""&gt; &lt;em&gt; &lt;i&gt; &lt;q cite=""&gt; &lt;strike&gt; &lt;strong&gt;</span>'),
            HTML('<hr>'),
            Field('image', css_class='input-block-level'),
            FormActions(
                Submit('submit', 'Voorbeeld tonen', css_class='btn')
            )
        )

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

    def clean_text(self):
        text = self.cleaned_data.get('text')

        text = bleach.clean(text, tags=BLEACH_TAGS, attributes=BLEACH_ATTRIBUTES, strip=True)

        return text

    def clean(self):
        cleaned_data = super(WriterPieceSubmitForm, self).clean()

        text = cleaned_data.get('text')
        genre = cleaned_data.get('genre')

        image = cleaned_data.get('image')

        if not text and (genre != 'Headline' and genre != 'Illustratie'):
            raise ValidationError("Schrijf een tekst (voor niet headline / illustratie bijdragen).")

        if not image and genre == 'Illustratie':
            raise ValidationError("Voeg een beeld toe voor illustratie bijdragen.")

        return cleaned_data

@login_required
def writer_piece_submit(request):
    player = Player.objects.get(user=request.user)

    if player.role == 'WRITER':
        if request.method == 'POST':
            save = request.POST.get('save', '') == 'save'
            edit = request.POST.get('save', '') == 'edit'
            
            pieceid = request.POST.get('pieceid', '')

            if not (edit or save):
                if pieceid:
                    piece = Piece.objects.get(id=pieceid)
                    form = WriterPieceSubmitForm(request.POST, request.FILES, instance=piece)
                else:
                    form = WriterPieceSubmitForm(request.POST, request.FILES)

                if form.is_valid():
                    piece = form.save(commit=False)

                    piece.deadline = datetime.datetime.utcnow().replace(tzinfo=utc)
                    piece.status = 'PASTDUE'
                    piece.writer = player
                    piece.save()

                    return render_to_response('boogie/piece_submit_preview.html', {
                        'piece': piece
                    }, RequestContext(request))
                else:
                    pass # Fall through
            elif edit and pieceid:
                # Reentry of existing piece to edit
                piece = Piece.objects.get(id=pieceid)

                form = WriterPieceSubmitForm(instance=piece)
            elif save and pieceid:
                # Save of existing piece to edit
                piece = Piece.objects.get(id=pieceid)

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

        return render_to_response('boogie/writer_piece_submit.html', {
            'form': form
        }, RequestContext(request))
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

            # Reset the deadline for the piece that needs work
            piece.deadline = datetime.datetime.utcnow().replace(tzinfo=utc) + datetime.timedelta(days=7)

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
    return HttpResponseRedirect(reverse('index'))

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
                Submit('submit', 'Bewaren', css_class='btn')
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

    order = request.GET.get('order', '-datepublished')

    t = loader.get_template('boogie/character_profile.html')

    c = RequestContext(request, {
        'character': character,
        'order': order,
        'pieces': Piece.objects.filter(status='APPROVED', character=character).order_by(order)
    })

    return HttpResponse(t.render(c))
