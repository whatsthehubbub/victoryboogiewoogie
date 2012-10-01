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
    
    def __unicode__(self):
        return self.title
    

class Piece(models.Model):
    topic = models.ForeignKey(Topic)
    
    writer = models.ForeignKey(Player)
    
    text = models.TextField(blank=True)
    new_topic = models.CharField(max_length=255, blank=True)
    
    status = models.CharField(max_length=255, choices=(('ASSIGNED', 'toegekend'), ('SUBMITTED', 'ingediend'), ('APPROVED', 'goedgekeurd'), ('REJECTED', 'afgekeurd')), default='ASSIGNED')
    
    rejection_reason = models.TextField(blank=True)
    
    rating = models.IntegerField(default=0)
    
    def __unicode__(self):
        return self.text