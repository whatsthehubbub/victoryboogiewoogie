from django.contrib import admin
from boogie.models import *

class PlayerAdmin(admin.ModelAdmin):
    list_display = ('user', 'pseudonym')
admin.site.register(Player, PlayerAdmin)

class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'pool', 'slug', 'piece_count', 'piece_threshold')
    prepopulated_fields = {"slug": ("title",)}
admin.site.register(Topic, TopicAdmin)

class PieceAdmin(admin.ModelAdmin):
    list_display = ('topic', 'frontpage', 'writer', 'genre', 'text', 'new_topic', 'status', 'rejection_reason', 'rating')
admin.site.register(Piece, PieceAdmin)
