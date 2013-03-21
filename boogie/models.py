# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.timezone import utc
from django.db.models import Min, Max
from django.conf import settings
from django.template.defaultfilters import slugify

from boogie import tasks

import logging

logger = logging.getLogger('sake')

import datetime
import math

class Player(models.Model):
    class Meta:
        verbose_name = u'Speler'
        verbose_name_plural = u'Spelers'

    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)

    user = models.OneToOneField(User)
    role = models.CharField(max_length=255, choices=(('PLAYER', 'player'), ('WRITER', 'schrijver')), default='PLAYER')

    # Player fields
    pseudonym = models.CharField(max_length=20, blank=True, verbose_name='Pennaam')
    onelinebio = models.CharField(max_length=255, blank=True, verbose_name="Korte biografie")

    # Write a piece about a character on next assignment
    piece_about_character = models.ForeignKey('Character', null=True, blank=True, help_text='De volgende keer dat de speler een stukje schrijft gaat het over dit karakter.')

    # E-mail notifications
    send_emails = models.BooleanField(default=True, verbose_name=u'Stuur me e-mail')
    emails_unsubscribe_hash = models.CharField(max_length=255, blank=True)

    def get_new_assignment(self):
        if self.role == 'WRITER':
            return # Writers don't get new assignments this way
        else:
            # TODO Check if you can get a new topic for which you are already writing
            new_topic = Topic.objects.exclude(archived=True).exclude(pool='WRITER').order_by('?')[0]

            # If the piece_about_character field is set, the next assignment is going to be about this character
            if self.piece_about_character:
                character = self.piece_about_character
                self.piece_about_character = None
                self.save()
            else:
                character = None

            deadline = datetime.datetime.utcnow().replace(tzinfo=utc) + datetime.timedelta(days=7)
            piece = Piece.objects.create(topic=new_topic, deadline=deadline, writer=self, genre='Proza', character=character)

            Notification.objects.create_new_assignment_notification(self, piece)

            return piece

    def pieces(self):
        return Piece.objects.filter(writer=self).order_by('-datepublished')

    def get_name(self):
        if self.pseudonym:
            return self.pseudonym
        else:
            return self.user.email

    def __unicode__(self):
        return self.user.username

    def update_unsubscribe_hash(self):
        import uuid
        self.emails_unsubscribe_hash = uuid.uuid4().hex

    def email(self):
        return self.user.email

    @models.permalink
    def get_absolute_url(self):
        return ('player_profile', [self.user.username])


# Code to create new player classes after registration
from registration.signals import user_activated

def activate_player(sender, user, request, **kwarg):
    player = Player.objects.get(user=user)
    player.get_new_assignment()
user_activated.connect(activate_player)


class Character(models.Model):
    class Meta:
        verbose_name = u'Personage'
        verbose_name_plural = u'Personages'

    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)

    name = models.CharField(max_length=255, help_text='Naam van het personage')
    onelinebio = models.CharField(max_length=255, blank=True)

    biography = models.TextField(blank=True)

    avatar = models.ImageField(blank=True, upload_to='characters', help_text="Avatars moeten in 400x400px worden ingesteld")

    def __unicode__(self):
        return self.name

    @models.permalink
    def get_absolute_url(self):
        return reverse('character_profile', args=(self.id,))

    def pieces(self):
        return Piece.objects.filter(status='APPROVED', character=self).order_by('-datepublished')


class PreLaunchEmail(models.Model):
    class Meta:
        verbose_name = u'Aangemelde e-mail'
        verbose_name_plural = u'Aangemelde e-mails'

    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)

    email = models.EmailField(verbose_name=u'E-mail')


from django.core.mail import EmailMessage

class NotificationManager(models.Manager):
    def create_new_assignment_notification(self, player, piece):
        return Notification.objects.create(identifier='player-new-assignment', for_player=player, message='''Je mag een nieuwe bijdrage schrijven. Ga naar <a href="http://www.gidsgame.nl%s">de schrijfafdeling</a>.''' % reverse('piece_submit'))

    def create_new_summary_notification(self, player, summary):
        return Notification.objects.create(identifier='new-summary', for_player=player, message='''Er is een nieuwe samenvatting geplaatst. <a href="http://www.gidsgame.nl%s">Lees hem direct hier</a>.''' % summary.get_absolute_url())

    def create_new_accepted_notification(self, player, piece):
        return Notification.objects.create(identifier='player-piece-accepted', for_player=player, message='''Je bijdrage is goedgekeurd! <a href="http://www.gidsgame.nl%s">Lees hem direct hier</a>.''' % piece.get_absolute_url())

    def create_new_needswork_notification(self, player, piece):
        return Notification.objects.create(identifier='player-piece-accepted', for_player=player, message='''Er moet nog wat aan je bijdrage gebeuren. <a href="http://www.gidsgame.nl%s">Probeer het opnieuw</a> met de feedback.''' % reverse('piece_submit'))

    def create_new_rejected_notification(self, player, piece):
        return Notification.objects.create(identifier='player-piece-accepted', for_player=player, message='''Je bijdrage is helaas afgekeurd. Probeer het opnieuw met je volgende opdracht.''')

    def new_notifications_for_player(self, player):
        return Notification.objects.filter(for_player=player).filter(datecreated__gte=player.user.last_login).count()

class Notification(models.Model):
    class Meta:
        verbose_name = u'Bericht'
        verbose_name_plural = u'Berichten'

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
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = self.for_player.user.email

            content = self.message + '<br><br>' + self.get_email_footer()

            try:
                msg = EmailMessage(subject, content, from_email, [to_email])
                msg.content_subtype = 'html'
                msg.send()
                logger.info('Sent e-mail to %s', to_email)
            except:
                logger.error('Could not send e-mail to %s', to_email)

    def get_email_footer(self):
        if not self.for_player.emails_unsubscribe_hash:
            self.for_player.update_unsubscribe_hash()
            self.for_player.save()

        return '''Deze e-mail is verstuurd door <a href="http://www.gidsgame.nl/">Victory Boogie Woogie</a>. Om je direct af te melden van verdere e-mails kan je je <a href="http://www.gidsgame.nl%s">met één klik uitschrijven</a>.''' % reverse('player_unsubscribe', args=(self.for_player.emails_unsubscribe_hash,))

    def get_subject(self):
        # TODO modify subjects based on notification type
        if self.identifier == 'bla':
            return ''
        else:
            return 'Nieuw bericht van Victory Boogie Woogie'


class Topic(models.Model):
    class Meta:
        verbose_name = u'Onderwerp'
        verbose_name_plural = u'Onderwerpen'

    title = models.CharField(max_length=255)
    slug = models.SlugField()
    
    pool = models.CharField(max_length=255, choices=(('PLAYER', 'player'), ('WRITER', 'schrijver')), default='WRITER')
    
    archived = models.BooleanField(default=False)

    # Counts of pieces written and pieces needed for a pool change
    piece_count = models.IntegerField(default=0)
    
    def approved_pieces(self):
        return self.piece_set.filter(status='APPROVED')
    
    def approved_pieces_since(self):
        # TODO the time since last is hard coded (so if we change it, change it here too)
        last_time = datetime.datetime.utcnow().replace(tzinfo=utc) - datetime.timedelta(days=1)

        return self.piece_set.filter(status='APPROVED').filter(datepublished__gt=last_time).count()

    def __unicode__(self):
        return self.title

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
    class Meta:
        verbose_name = u'Bijdrage'
        verbose_name_plural = u'Bijdragen'

    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)
    
    topic = models.ForeignKey(Topic, verbose_name=u'Onderwerp')
    deadline = models.DateTimeField()
    writer = models.ForeignKey(Player)

    character = models.ForeignKey(Character, blank=True, null=True, verbose_name=u'Personage')

    image = models.ImageField(blank=True, upload_to='piece_images', verbose_name='Illustratie')
    
    genre = models.CharField(max_length=255, blank=True, choices=PIECE_GENRE_CHOICES)
    title = models.CharField(max_length=255, blank=True, verbose_name="Titel")
    text = models.TextField(blank=True, verbose_name="Tekst")
    new_topic = models.CharField(max_length=255, blank=True, verbose_name="Nieuw onderwerp")
    
    status = models.CharField(max_length=255, choices=(
                    ('ASSIGNED', 'toegekend'),
                    ('SUBMITTED', 'ingediend'),
                    ('APPROVED', 'goedgekeurd'),
                    ('WAITING', 'wacht op publicatie'),
                    ('NEEDSWORK', 'needs work'),
                    ('REJECTED', 'afgekeurd'),
                    ('PASTDUE', 'deadline verstreken')), default='ASSIGNED')

    datepublished = models.DateTimeField(blank=True, null=True)
    
    rejection_reason = models.TextField(blank=True)
    

    # Visible on the frontpage or not?
    frontpage = models.BooleanField(default=False)
    # Highlighted on the front page or not?
    highlight = models.BooleanField(default=False)
    
    def __unicode__(self):
        return '%s by %s' % (unicode(self.topic), unicode(self.writer))


    @models.permalink
    def get_absolute_url(self):
        return ('boogie.views.piece_detail', [self.id])

    def vote_up(self, player):
        try:
            PieceVote.objects.get(player=player, piece=self)
            # Vote exists already so we don't do anything
        except:
            # If the vote does not exist, we create one
            PieceVote.objects.create(player=player, piece=self)

    def vote_up_undo(self, player):
        try:
            vote = PieceVote.objects.get(player=player, piece=self)
            vote.delete()
        except:
            logger.info('Tried to undo non-existent vote')


    score_cache = models.FloatField(default=0.0)

    def score(self):
        # (likes - 1) / (hours_since_publication + 2) ^ 1.5

        if self.status == 'APPROVED':
            diff = datetime.datetime.utcnow().replace(tzinfo=utc) - self.datepublished
            hours = diff.days * 24 + diff.seconds / 3600
            likes = PieceVote.objects.filter(piece=self).count()

            # Changed (likes - 1) so we won't get negative results
            return (likes + 1) / math.pow(hours+2, 1.5)
        else:
            return 0

    def update_score_cache(self):
        self.score_cache = self.score()
        self.save()

    def get_human_score(self):
        def scale(val, src, dst):
            """
            Scale the given value from the scale of src to the scale of dst.
            """
            try:
                return ((val - src[0]) / (src[1]-src[0])) * (dst[1]-dst[0]) + dst[0]
            except ZeroDivisionError:
                return 0.0

        min_max = Piece.objects.aggregate(Min('score_cache'), Max('score_cache'))
        min_score = min_max['score_cache__min']
        max_score = min_max['score_cache__max']

        return scale(self.score_cache, [min_score, max_score], [1.0, 10.0])

    def get_next_piece(self):
        try:
            return Piece.objects.filter(status='APPROVED', datepublished__gt=self.datepublished).order_by('datepublished')[0]
        except:
            return None

    def get_previous_piece(self):
        try:
            return Piece.objects.filter(status='APPROVED', datepublished__lt=self.datepublished).order_by('-datepublished')[0]
        except:
            return None

    def get_next_piece_by_topic(self):
        try:
            return Piece.objects.filter(status='APPROVED', topic=self.topic, datepublished__gt=self.datepublished).order_by('datepublished')[0]
        except:
            return None

    def get_previous_piece_by_topic(self):
        try:
            return Piece.objects.filter(status='APPROVED', topic=self.topic, datepublished__lt=self.datepublished).order_by('-datepublished')[0]
        except:
            return None

    def get_next_piece_by_character(self):
        try:
            return Piece.objects.filter(status='APPROVED', character=self.character, datepublished__gt=self.datepublished).order_by('datepublished')[0]
        except:
            return None

    def get_previous_piece_by_character(self):
        try:
            return Piece.objects.filter(status='APPROVED', character=self.character, datepublished__lt=self.datepublished).order_by('-datepublished')[0]
        except:
            return None


    def approve(self):
        self.status = 'APPROVED'

        self.datepublished = datetime.datetime.utcnow().replace(tzinfo=utc)
            
        self.topic.piece_count += 1
        self.topic.save()

        Notification.objects.create_new_accepted_notification(self.writer, self)

        # Also we need to create a new topic based on this approved piece
        if self.new_topic:
            t = Topic.objects.create(pool="PLAYER", title=self.new_topic, slug=slugify(self.new_topic))
            t.save()

        self.save()


class PieceVote(models.Model):
    class Meta:
        verbose_name = u'Stem'
        verbose_name_plural = u'Stemmen'

    # This counts votes up
    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)

    player = models.ForeignKey(Player)
    piece = models.ForeignKey(Piece)


class Advertisement(models.Model):
    class Meta:
        verbose_name = u'Advertentie'
        verbose_name_plural = u'Advertenties'

    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)

    image = models.ImageField(blank=True, upload_to='advertisements', help_text="")

    url = models.URLField(blank=True)
    sender = models.CharField(blank=True, max_length=255)

    rank = models.IntegerField(default=1)

    def __unicode__(self):
        return self.sender

    def get_absolute_url(self):
        return self.url


class Summary(models.Model):
    class Meta:
        verbose_name = u'Samenvatting'
        verbose_name_plural = u'Samenvattingen'

    datecreated = models.DateTimeField(auto_now_add=True)
    datechanged = models.DateTimeField(auto_now=True)

    content = models.TextField()

    def __unicode__(self):
        return self.content

    def save(self, *args, **kwargs):
        # Create a notification of this summary for all players only if this summary is new
        # This enables us to update

        createNotification = False
        if self.pk is None:
            # PK is only None on a new object before save
            createNotification = True

        super(Summary, self).save(*args, **kwargs)

        if createNotification:
            tasks.create_summary_notifications_for_all_players.apply_async(args=[self])

    def get_absolute_url(self):
        return reverse('summary') + ('#samenvatting-%d' % self.id)


class GameManager(models.Manager):
    def get_latest_game(self):
        # This is the active game
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

    # Used to turn on/off the pre launch screen
    started = models.BooleanField(default=False)

    # Active is past week 10
    # active = models.BooleanField(default=True)

    days_between_reassign = models.IntegerField(default=1)

    objects = GameManager()

    def __unicode__(self):
        return "Game with start: %s" % self.start_date.isoformat()

    def weeks_since_start(self):
        today = datetime.date.today()

        if today >= self.start_date:
            delta = today - self.start_date

            return (delta.days / 7) + 1

        return 0

    def over(self):
        if self.weeks_since_start() > 10:
            return True
        else:
            return False

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
