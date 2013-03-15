from django.contrib import admin
from boogie.models import *

class PlayerAdmin(admin.ModelAdmin):
    list_display = ('user', 'pseudonym', 'role', 'send_emails')
admin.site.register(Player, PlayerAdmin)

class CharacterAdmin(admin.ModelAdmin):
    list_display = ('name', 'onelinebio')
admin.site.register(Character, CharacterAdmin)


def archive_topic(modeladmin, request, queryset):
    queryset.update(archived=True)
archive_topic.short_description = "Archiveer geselecteerde onderwerpen"

class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'pool', 'slug', 'archived', 'piece_count')
    prepopulated_fields = {"slug": ("title",)}
    actions = [archive_topic]
admin.site.register(Topic, TopicAdmin)

class PieceAdmin(admin.ModelAdmin):
    list_display = ('topic', 'datechanged', 'score_cache', 'writer', 'genre', 'title', 'datepublished', 'status', 'character')

    date_hierarchy = 'datechanged'
    list_filter = ('genre', 'frontpage', 'topic', 'status', 'character')

admin.site.register(Piece, PieceAdmin)

class PieceVoteAdmin(admin.ModelAdmin):
    list_display = ('player', 'piece')
admin.site.register(PieceVote, PieceVoteAdmin)

class AdvertisementAdmin(admin.ModelAdmin):
    list_display = ('datecreated', 'sender', 'rank')
admin.site.register(Advertisement, AdvertisementAdmin)

class SummaryAdmin(admin.ModelAdmin):
    list_display = ('datecreated', 'content')
admin.site.register(Summary, SummaryAdmin)

class PreLaunchEmailAdmin(admin.ModelAdmin):
    list_display = ('email', )
admin.site.register(PreLaunchEmail, PreLaunchEmailAdmin)

class NotificationAdmin(admin.ModelAdmin):
    list_display = ('datecreated', 'identifier', 'for_player', 'message')
admin.site.register(Notification, NotificationAdmin)

class GameAdmin(admin.ModelAdmin):
    list_display = ('start_date', 'started', 'days_between_reassign')
admin.site.register(Game, GameAdmin)
