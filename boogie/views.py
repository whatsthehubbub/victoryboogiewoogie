# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.http import require_POST
from django.template import RequestContext, loader
from django.forms import ModelForm
from django.core.urlresolvers import reverse

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from boogie.models import *

from boogie import tasks

def index(request):
    t = loader.get_template('boogie/index.html')
    
    c = RequestContext(request, {
            'topics': Topic.objects.all(),
            'pieces': Piece.objects.exclude(frontpage=False), # TODO check if the piece is approved?
    })
    return HttpResponse(t.render(c))
    
def topic_list(request):
    t = loader.get_template('boogie/topic_list.html')
    
    c = RequestContext(request, {
            'writer_topics': Topic.objects.filter(pool='WRITER'),
            'player_topics': Topic.objects.filter(pool='PLAYER')
    })
    return HttpResponse(t.render(c))
    
def topic_detail(request, topicid, slug):
    t = loader.get_template('boogie/topic_detail.html')
    
    order = request.GET.get('order', '-rating')

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
            'pieces': Piece.objects.all()
    })
    return HttpResponse(t.render(c))

def piece_detail(request, id):
    t = loader.get_template('boogie/piece_detail.html')

    c = RequestContext(request, {
            'piece': Piece.objects.get(id=id)
    })
    return HttpResponse(t.render(c))

class PieceSubmitForm(ModelForm):
    class Meta:
        model = Piece
        fields = ('genre', 'text', 'new_topic')

@login_required
def piece_submit(request):
    t = loader.get_template('boogie/piece_submit.html')
    
    # piece = Piece.objects.get(id=piece_id)
    assignments = Piece.objects.filter(status='ASSIGNED').filter(writer__user=request.user)
    if assignments:
        piece = assignments[0]

        if request.method == 'POST':
            form = PieceSubmitForm(request.POST, instance=piece)
            if form.is_valid():
                form.instance.status = 'SUBMITTED'
                form.save()
                
                # Give this person a new assignment
                tasks.get_new_assignment.delay(form.instance.writer)

                return HttpResponseRedirect(reverse('boogie.views.piece_detail', args=[piece.id]))
        else:
            form = PieceSubmitForm(instance=piece)
    else:
        form = None
    
    c = RequestContext(request, {
            'form': form
    })
    return HttpResponse(t.render(c))

# TODO proper access controls
@require_POST
@login_required
def piece_validate(request, piece_id):
    piece = Piece.objects.get(id=piece_id)
    
    valid = request.POST.get('ok', '')
    
    if valid == 'yes':
        piece.status = 'APPROVED'
        
        piece.topic.piece_count += 1
        piece.topic.save()

        # Check whether this topic should switch pools back to writers
        tasks.check_topic_pool.delay(piece.topic)

    elif valid == 'no':
        piece.rejection_reason = request.POST.get('reason', '')
        piece.status = 'REJECTED'

    piece.save()
        
    return HttpResponseRedirect(reverse('piece_queue'))

@login_required
def pieces_assign(request):
    players_without = Player.objects.exclude(piece__status='ASSIGNED')

    for player in players_without:
        player.get_new_assignment()

    return HttpResponse('1')

@require_POST
def piece_vote_up(request, piece_id):
    piece = Piece.objects.get(id=piece_id)
    # TODO implement a suitable voting algorithm
    
    
def piece_queue(request):
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
    
    if player.role == 'PLAYER':
        t = loader.get_template('boogie/player_profile.html')

        # Show the approved pieces in any case
        c['approved_pieces'] = player.pieces().filter(status="APPROVED")

        if request.user.username == name:
            c['assigned_pieces'] = player.pieces().filter(status="ASSIGNED")
            c['submitted_pieces'] = player.pieces().filter(status="SUBMITTED")

            c['needswork_pieces'] = player.pieces().filter(status="NEEDSWORK")
            c['rejected_pieces'] = player.pieces().filter(status="REJECTED")
        
        return HttpResponse(t.render(c))


class UserProfileForm(ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name')

class PlayerProfileForm(ModelForm):
    class Meta:
        model = Player
        fields = ('pseudonym', 'biography')

def player_profile_edit(request, name):
    t = loader.get_template('boogie/player_profile_edit.html')

    # TODO check if you can edit your profile
    player = Player.objects.get(user__username=name)

    if request.method == 'POST':
        userform = UserProfileForm(request.POST, instance=player.user)
        profileform = PlayerProfileForm(request.POST, instance=player)

        if userform.is_valid() and profileform.is_valid():
            userform.save()
            profileform.save()

            return HttpResponseRedirect(reverse('boogie.views.player_profile', args=[name]))
    else:
        userform = UserProfileForm(instance=player.user)
        playerform = PlayerProfileForm(instance=player)

    c = RequestContext(request, {
        'userform': userform,
        'playerform': playerform
    })

    return HttpResponse(t.render(c))


def writers(request):
    writers = Player.objects.filter(role='WRITER')

    t = loader.get_template('boogie/writers.html')
    c = RequestContext(request, {
        'writers': writers
    })

    return HttpResponse(t.render(c))

def writer_profile(request, name):
    player = Player.objects.get(user__username=name)

    if player.role == 'WRITER':
        t = loader.get_template('boogie/writer_profile.html')

        c = RequestContext(request, {
            'writer': player
        })

        return HttpResponse(t.render(c))

