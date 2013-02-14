# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.timezone import utc

import logging

logger = logging.getLogger('sake')

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
    onelinebio = models.CharField(max_length=255, blank=True)

    # E-mail notifications
    send_emails = models.BooleanField(default=True)

    def get_new_assignment(self):
        if self.role == 'WRITER':
            return # Writers don't get new assignments this way
        else:
            # TODO Check if you can get a new topic for which you are already writing
            new_topic = Topic.objects.exclude(pool='WRITER').order_by('?')[0]

            deadline = datetime.datetime.utcnow().replace(tzinfo=utc) + datetime.timedelta(days=7)
            piece = Piece.objects.create(topic=new_topic, deadline=deadline, writer=self)

            Notification.objects.create_new_assignment_notification(self, piece)

            return piece

    def pieces(self):
        return Piece.objects.filter(writer=self).order_by('-datepublished')

    def get_name(self):
        if self.pseudonym:
            return self.pseudonym
        else:
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
    
    # TODO Also fill in unsubscribe hash

    player.get_new_assignment()
user_registered.connect(create_player)


class Character(models.Model):
    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=255, help_text='Naam van het personage')
    onelinebio = models.CharField(max_length=255, blank=True)
    # TODO same with the large and small portrait fields here, though they may be in the assets already

    # Common fields
    biography = models.TextField(blank=True)

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        if self.role == 'WRITER':
            return ('writer_profile', [self.user.username])
        else:
            return ('player_profile', [self.user.username])


class PreLaunchEmail(models.Model):
    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)

    email = models.EmailField()


from django.core.mail import EmailMessage

class NotificationManager(models.Manager):
    def create_new_assignment_notification(self, player, piece):
        return Notification.objects.create(identifier='player-new-assignment', for_player=player, message='''Je mag een nieuwe bijdrage schrijven. Ga naar <a href="http://www.gidsgame.nl/pieces/submit/">de schrijfafdeling</a>.''')

    def create_new_summary_notification(self, player, summary):
        return Notification.objects.create(identifier='new-summary', for_player=player, message='''Er is een nieuwe samenvatting geplaatst. Lees hem direct <a href="http://www.gidsgame.nl%s">hier</a>.''' % summary.get_absolute_url())

    def create_new_accepted_notification(self, player, piece):
        return Notification.objects.create(identifier='player-piece-accepted', for_player=player, message='''Je bijdrage is goedgekeurd. Lees hem direct op <a href="http://www.gidsgame.nl%s">de site.</a>''' % piece.get_absolute_url())

    def create_new_needswork_notification(self, player, piece):
        return Notification.objects.create(identifier='player-piece-accepted', for_player=player, message='''Er moet nog wat aan je bijdrage gebeuren. <a href="http://www.gidsgame.nl/pieces/submit/">Probeer het opnieuw</a> met de feedback.''')

    def create_new_rejected_notification(self, player, piece):
        return Notification.objects.create(identifier='player-piece-accepted', for_player=player, message='''Je bijdrage is helaas afgekeurd. Probeer het opnieuw met je volgende opdracht.''')

class Notification(models.Model):
    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)

    identifier = models.CharField(max_length=255)

    for_player = models.ForeignKey(Player)
    message = models.TextField()

    objects = NotificationManager()

    def save(self, *args, **kwargs):
        # Do e-mail sending here only if this is a new object
        if self.pk is None:
            self.send_email()

        super(Notification, self).save(*args, **kwargs)


    def send_email(self):
        if self.for_player.send_emails:
            subject = self.get_subject()
            from_email = 'Mailman@gidsgame.nl'
            to_email = self.for_player.user.email

            content = self.message

            try:
                msg = EmailMessage(subject, content, from_email, [to_email])
                msg.content_subtype = 'html'
                msg.send()
                logger.info('Sent e-mail to %s', to_email)
            except:
                logger.error('Could not send e-mail to %s', to_email)


    def get_subject(self):
        if self.identifier == 'bla':
            return ''
        else:
            return 'Nieuw bericht van de Gids'


class Topic(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField()
    
    pool = models.CharField(max_length=255, choices=(('PLAYER', 'player'), ('WRITER', 'schrijver')), default='WRITER')
    
    archived = models.BooleanField(default=False)

    # Counts of pieces written and pieces needed for a pool change
    piece_count = models.IntegerField(default=0)

    # A function of the number of writers
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

    def get_latest_piece(self):
        try:
            return self.approved_pieces()[0]
        except IndexError:
            return None

    @models.permalink
    def get_absolute_url(self):
        return ('boogie.views.topic_detail', [self.id, self.slug])
    

PIECE_GENRE_CHOICES = (('Headline', 'Headline'), ('Proza', 'Proza'), ('Poezie', 'Poëzie'), ('Essay', 'Essay'), ('Illustratie', 'Illustratie'))

class Piece(models.Model):
    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)
    
    topic = models.ForeignKey(Topic)
    deadline = models.DateTimeField()
    writer = models.ForeignKey(Player)

    character = models.ForeignKey(Character, blank=True, null=True)

    image = models.ImageField(blank=True, upload_to='piece_images')
    
    genre = models.CharField(max_length=255, blank=True, choices=PIECE_GENRE_CHOICES)
    title = models.CharField(max_length=255)
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
    

    # Visible on the frontpage or not?
    frontpage = models.BooleanField(default=False)
    
    def __unicode__(self):
        return '%s by %s' % (str(self.topic), str(self.writer))


    @models.permalink
    def get_absolute_url(self):
        return ('boogie.views.piece_detail', [self.id])

    def vote_up(self, player):
        try:
            vote = PieceVote.objects.get(player=player, piece=self)
            # Vote exists already so we don't do anything
        except:
            # If the vote does not exist, we create one
            PieceVote.objects.create(player=player, piece=self)

    def vote_up_undo(self, player):
        try:
            vote = PieceVote.objects.get(player=player, piece=self)
            vote.delete()
        except:
            print 'fail'
            logger.info('Tried to undo non-existent vote')


    score_cache = models.FloatField(default=0.0)

    def score(self):
        # (likes - 1) / (hours_since_publication + 2) ^ 1.5

        if self.status == 'APPROVED':
            timedelta = datetime.datetime.utcnow().replace(tzinfo=utc) - self.datepublished
            hours = timedelta.days * 24 + timedelta.seconds / 3600
            likes = PieceVote.objects.filter(piece=self).count()

            # Changed (likes - 1) so we won't get negative results
            return (likes + 1) / math.pow(hours+2, 1.5)
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

    # TODO rewrite this to a get()
    @staticmethod
    def vote_exists(player, piece):
        return PieceVote.objects.filter(player=player, piece=piece).count() > 0



class Summary(models.Model):
    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)

    content = models.TextField()

    def __unicode__(self):
        return self.content

    def save(self, *args, **kwargs):
        # Create a notification of this summary for all players only if this summary is new
        # This enables us to update
        if self.pk is None:
            # TODO defer this to the celery queue
            for player in Player.objects.all():
                Notification.objects.create_new_summary_notification(player, self)

        super(Summary, self).save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('summary') + '#summary_' + str(self.id)


class GameManager(models.Manager):
    def get_latest_game(self):
        # TODO cache this call

        games = Game.objects.all().order_by('-start_date')

        if games:
            return games[0]
        else:
            return Game.objects.create(start_date=datetime.date.today())


class Game(models.Model):
    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)

    start_date = models.DateField()

    days_between_reassign = models.IntegerField(default=1)

    objects = GameManager()

    def __unicode__(self):
        return "Game with start: %s" % str(self.start_date)


    def save(self, *args, **kwargs):
        super(Game, self).save(*args, **kwargs)

        # TODO this updates the task on every game updated and should only do so on the current one
        try:
            from djcelery.models import PeriodicTask
            task = PeriodicTask.objects.get(name='new-assignments')

            task.enabled = False
            task.save()

            task.interval.every = self.days_between_reassign * 24 * 60 * 60
            task.interval.period = 'seconds'
            task.interval.save()

            task.enabled = True
            task.save()
        except:
            logger.error("Failed to update PeriodicTask after Game save")
