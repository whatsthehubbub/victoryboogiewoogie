# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import Count
from django.contrib.auth.models import User

import datetime


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

    def get_new_assignment(self):
        if self.role == 'WRITER':
            return # Writers don't get new assignments this way

        empty_topics = Topic.objects.exclude(pool='WRITER').exclude(piece__writer=self).exclude(piece__status='APPROVED').order_by('?')

        if empty_topics:
            # If there are topics that don't have an assignee, get one of those
            # TODO remove this query because at large numbers this is bound not to happen anyway
            # TODO figure out a more generic query to catch both cases
            new_topic = empty_topics[0]
        else:
            topics_with_piece_count = Topic.objects.exclude(pool='WRITER').filter(piece__status='APPROVED').annotate(num_pieces=Count('piece')).order_by('num_pieces')

            new_topic = topics_with_piece_count[0]

        # TODO figure out what to do with the deadline later
        deadline = datetime.datetime.now() + datetime.timedelta(days=7)
        return Piece.objects.create(topic=new_topic, deadline=deadline, writer=self)

    def pieces(self):
        return Piece.objects.filter(writer=self)

    def get_name(self):
        if self.role == 'PLAYER':
            return self.pseudonym
        else:
            return self.character_name

    def __unicode__(self):
        return self.user.username


# Code to create new player classes after registration
from registration.signals import user_registered

def create_player(sender, user, request, **kwarg):
    Player.objects.create(user=user)
    # new players get an assignment directly
    # TODO figure out what to do about created writers
    player.get_new_assignment()
user_registered.connect(create_player)



class Topic(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    
    pool = models.CharField(max_length=255, choices=(('PLAYER', 'player'), ('WRITER', 'schrijver')), default='WRITER')
    
    archived = models.BooleanField(default=False)

    # Counts of pieces written and pieces needed for a pool change
    piece_count = models.IntegerField(default=0)

    # TODO has to be a function of number of writers
    # and how much work those writers have to do right now
    piece_threshold = models.IntegerField(default=3)
    
    def approved_pieces(self):
        return self.piece_set.filter(status='APPROVED')
    
    def __unicode__(self):
        return self.title
    
    def check_pool(self):
        if self.pool == 'PLAYER' and self.piece_count >= self.piece_threshold:
            self.pool = 'WRITER'
            self.save()

            return True
        return False

    @models.permalink
    def get_absolute_url(self):
        return ('boogie.views.topic_detail', [self.id, self.slug])
    

class Piece(models.Model):
    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)
    
    topic = models.ForeignKey(Topic)
    deadline = models.DateTimeField()
    writer = models.ForeignKey(Player)
    
    genre = models.CharField(max_length=255, blank=True, choices=(('Headline', 'Headline'), ('Proza', 'Proza'), ('Poezie', 'Poëzie'), ('Essay', 'Essay')))
    text = models.TextField(blank=True)
    new_topic = models.CharField(max_length=255, blank=True)
    
    status = models.CharField(max_length=255, choices=(
                    ('ASSIGNED', 'toegekend'), 
                    ('SUBMITTED', 'ingediend'), 
                    ('APPROVED', 'goedgekeurd'), 
                    ('NEEDSWORK', 'needs work'), 
                    ('REJECTED', 'afgekeurd')), default='ASSIGNED')

    datepublished = models.DateTimeField(blank=True, null=True)
    
    rejection_reason = models.TextField(blank=True)
    
    rating = models.IntegerField(default=0)

    # Visible on the frontpage or not?
    frontpage = models.BooleanField(default=False)
    
    def __unicode__(self):
        return '%s by %s' % (str(self.topic), str(self.writer))


    @models.permalink
    def get_absolute_url(self):
        return ('boogie.views.piece_detail', [self.id])


class Summary(models.Model):
    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)

    content = models.TextField()

    def __unicode__(self):
        return self.content