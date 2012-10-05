# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext, loader
from django.forms import ModelForm
from django.core.urlresolvers import reverse

from boogie.models import *

def index(request):
    t = loader.get_template('boogie/index.html')
    
    c = RequestContext(request, {
            'topics': Topic.objects.all(),
            'pieces': Piece.objects.exclude(frontpage=False), # TODO check if the piece is approved?
            'assignments': Piece.objects.filter(status='ASSIGNED').filter(writer__user=request.user)
    })
    return HttpResponse(t.render(c))
    
def topic_list(request):
    t = loader.get_template('boogie/topic_list.html')
    
    c = RequestContext(request, {
            'writer_topics': Topic.objects.filter(pool='WRITER'),
            'player_topics': Topic.objects.filter(pool='PLAYER')
    })
    return HttpResponse(t.render(c))
    
def topic_detail(request, id, title):
    t = loader.get_template('boogie/topic_detail.html')
    
    order = request.GET.get('order', '-rating')

    topic = Topic.objects.get(id=id)

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
        fields = ('text', 'new_topic')

def piece_submit(request, piece_id):
    t = loader.get_template('boogie/piece_submit.html')
    
    piece = Piece.objects.get(id=piece_id)
    
    if request.method == 'POST':
        form = PieceSubmitForm(request.POST, instance=piece)
        if form.is_valid():
            form.instance.status = 'SUBMITTED'
            form.save()
            
            return HttpResponseRedirect(reverse('boogie.views.piece_detail', args=[piece.id]))
    else:
        form = PieceSubmitForm(instance=piece)
    
    c = RequestContext(request, {
            'form': form
    })
    return HttpResponse(t.render(c))

# TODO proper access controls
def piece_validate(request, piece_id):
    if request.method == 'POST':
        piece = Piece.objects.get(id=piece_id)
        
        valid = request.POST.get('ok', '')
        
        if valid == 'yes':
            piece.status = 'APPROVED'
            
            # Assuming that a piece here would always be from the non-writer pool
            piece.topic.pool = 'WRITER'
            piece.topic.save()
        elif valid == 'no':
            piece.rejection_reason = request.POST.get('reason', '')
            piece.status = 'REJECTED'
    
        piece.save()
        
    return HttpResponseRedirect(reverse('piece_queue'))
    
def piece_vote_up(request, piece_id):
    if request.method == 'POST':
        piece = Piece.objects.get(id=piece_id)
        # TODO implement a suitable voting algorithm
    
    
def piece_queue(request):
    t = loader.get_template('boogie/piece_queue.html')

    c = RequestContext(request, {
        'pieces': Piece.objects.filter(status='SUBMITTED').order_by('-datecreated')
    })
    return HttpResponse(t.render(c))


def writer_profile(request, name):
    player = Player.objects.get(user__username=name)

    t = loader.get_template('boogie/writer_profile.html')

    c = RequestContext(request, {
        'player': player
    })

    return HttpResponse(t.render(c))

