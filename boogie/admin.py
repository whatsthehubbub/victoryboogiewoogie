from django.contrib import admin
from boogie.models import *

class PlayerAdmin(admin.ModelAdmin):
    list_display = ('user', 'pseudonym', 'role', 'character_name',)
admin.site.register(Player, PlayerAdmin)

class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'pool', 'slug', 'piece_count', 'piece_threshold')
    prepopulated_fields = {"slug": ("title",)}
admin.site.register(Topic, TopicAdmin)

class PieceAdmin(admin.ModelAdmin):
    list_display = ('topic', 'frontpage', 'writer', 'genre', 'title', 'text', 'new_topic', 'status', 'rejection_reason', 'rating')
admin.site.register(Piece, PieceAdmin)

class PieceVoteAdmin(admin.ModelAdmin):
    list_display = ('player', 'piece')
admin.site.register(PieceVote, PieceVoteAdmin)

class SummaryAdmin(admin.ModelAdmin):
    list_display = ('datecreated', 'content')
admin.site.register(Summary, SummaryAdmin)
