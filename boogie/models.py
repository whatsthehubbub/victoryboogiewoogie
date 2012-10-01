from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

# Create your models here.

class Player(models.Model):
    user = models.OneToOneField(User)
    
    role = models.CharField(max_length=255, choices=(('PLAYER', 'player'), ('WRITER', 'schrijver')))
    
    def __unicode__(self):
        return self.user.username

class Topic(models.Model):
    title = models.CharField(max_length=255)
    
    pool = models.CharField(max_length=255, choices=(('PLAYER', 'player'), ('WRITER', 'schrijver')), default='WRITER')
    
    def approved_pieces(self):
        return self.piece_set.filter(status='APPROVED').order_by('-datechanged')
    
    def __unicode__(self):
        return self.title
    
    @models.permalink
    def get_absolute_url(self):
        return ('boogie.views.topic_detail', [self.id, self.title])
    

class Piece(models.Model):
    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)
    
    topic = models.ForeignKey(Topic)
    
    writer = models.ForeignKey(Player)
    
    text = models.TextField(blank=True)
    new_topic = models.CharField(max_length=255, blank=True)
    
    status = models.CharField(max_length=255, choices=(('ASSIGNED', 'toegekend'), ('SUBMITTED', 'ingediend'), ('APPROVED', 'goedgekeurd'), ('REJECTED', 'afgekeurd')), default='ASSIGNED')
    
    rejection_reason = models.TextField(blank=True)
    
    rating = models.IntegerField(default=0)
    
    def __unicode__(self):
        return self.text
        
    @models.permalink
    def get_absolute_url(self):
        return ('boogie.views.piece_detail', [self.id])