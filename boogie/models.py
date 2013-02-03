# -*- coding: utf-8 -*-
from django.db import models
from django.db.models import Count
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.timezone import utc

import datetime
import math

class Player(models.Model):
    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)

    user = models.OneToOneField(User)
    role = models.CharField(max_length=255, choices=(('PLAYER', 'player'), ('WRITER', 'schrijver')), default='PLAYER')

    
    avatar = models.ImageField(blank=True, upload_to='avatars')


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
        else:
            # TODO Check if you can get a new topic for which you are already writing
            new_topic = Topic.objects.exclude(pool='WRITER').order_by('?')[0]

            # TODO figure out what to do with the deadline later
            deadline = datetime.datetime.utcnow().replace(tzinfo=utc) + datetime.timedelta(days=7)
            return Piece.objects.create(topic=new_topic, deadline=deadline, writer=self)

    def pieces(self):
        return Piece.objects.filter(writer=self).order_by('-datepublished')

    def get_name(self):
        if self.role == 'PLAYER':
            if self.pseudonym:
                return self.pseudonym
        else:
            if self.character_name:
                return self.character_name
        return self.user.username

    def __unicode__(self):
        return self.user.username

    @models.permalink
    def get_absolute_url(self):
        if self.role == 'WRITER':
            return ('writer_profile', [self.user.username])
        else:
            return ('player_profile', [self.user.username])


# Code to create new player classes after registration
from registration.signals import user_registered

def create_player(sender, user, request, **kwarg):
    player = Player.objects.create(user=user) # Default role is player
    # new players get an assignment directly
    # TODO figure out what to do about created writers
    player.get_new_assignment()
user_registered.connect(create_player)


class PreLaunchEmail(models.Model):
    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)

    email = models.EmailField()


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
            self.piece_count = 0
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
    title = models.CharField(blank=True, max_length=255)
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

    def vote_up(self, player):
        if not PieceVote.vote_exists(player, self):
            PieceVote.objects.create(player=player, piece=self)

            # TODO do updating of metrics

    score_cache = models.FloatField(default=0.0)

    def score(self):
        # TODO change this into
        # (likes - 1) / (hours_since_publication + 2) ^ 1.5

        # TODO probably denormalize this into a database field
        if self.status == 'APPROVED':
            timedelta = datetime.datetime.utcnow().replace(tzinfo=utc) - self.datepublished
            hours = timedelta.days * 24 + timedelta.seconds / 3600
            likes = PieceVote.objects.filter(piece=self).count()

            return (likes - 1) / math.pow(hours+2, 1.5)
        else:
            return 0

    def update_score_cache(self):
        self.score_cache = self.score()
        self.save()


class PieceVote(models.Model):
    # This counts votes up
    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)

    player = models.ForeignKey(Player)
    piece = models.ForeignKey(Piece)

    @staticmethod
    def vote_exists(player, piece):
        return PieceVote.objects.filter(player=player, piece=piece).count() > 0



class Summary(models.Model):
    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)

    content = models.TextField()

    def __unicode__(self):
        return self.content

    def get_absolute_url(self):
        return reverse('summary') + '#summary_' + str(self.id)
