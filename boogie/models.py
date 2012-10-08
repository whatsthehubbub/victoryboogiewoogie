from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Player(models.Model):
    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)

    user = models.OneToOneField(User)
    role = models.CharField(max_length=255, choices=(('PLAYER', 'player'), ('WRITER', 'schrijver')), default='PLAYER')

    # TODO figure out where to store the avatar images
    # avatar = models.ImageField(blank=True)

    # Player fields
    pseudonym = models.CharField(max_length=255, blank=True, help_text='Pennaam')

    # Writer fields
    character_name = models.CharField(max_length=255, blank=True, help_text='Naam van het personage')
    onelinebio = models.CharField(max_length=255, blank=True)
    # TODO same with the large and small portrait fields here, though they may be in the assets already

    # Common fields
    biography = models.TextField(blank=True)

    def pieces(self):
        return Piece.objects.filter(writer=self)

    def __unicode__(self):
        return self.user.username


class Topic(models.Model):
    title = models.CharField(max_length=255)
    
    pool = models.CharField(max_length=255, choices=(('PLAYER', 'player'), ('WRITER', 'schrijver')), default='WRITER')
    
    archived = models.BooleanField(default=False)
    
    def approved_pieces(self):
        return self.piece_set.filter(status='APPROVED')
    
    def __unicode__(self):
        return self.title
    
    @models.permalink
    def get_absolute_url(self):
        return ('boogie.views.topic_detail', [self.id, self.title])
    

class Piece(models.Model):
    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)
    
    topic = models.ForeignKey(Topic)
    deadline = models.DateTimeField()    
    writer = models.ForeignKey(Player)
    
    text = models.TextField(blank=True)
    new_topic = models.CharField(max_length=255, blank=True)
    

    status = models.CharField(max_length=255, choices=(('ASSIGNED', 'toegekend'), ('SUBMITTED', 'ingediend'), ('APPROVED', 'goedgekeurd'), ('NEEDSWORK', 'needs work'), ('REJECTED', 'afgekeurd')), default='ASSIGNED')
    
    rejection_reason = models.TextField(blank=True)
    
    rating = models.IntegerField(default=0)

    # Visible on the frontpage or not?
    frontpage = models.BooleanField(default=False)
    
    def __unicode__(self):
        return self.text
        
    @models.permalink
    def get_absolute_url(self):
        return ('boogie.views.piece_detail', [self.id])

