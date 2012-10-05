from django.contrib import admin
from boogie.models import *

class PlayerAdmin(admin.ModelAdmin):
    list_display = ('user', 'pseudonym')
admin.site.register(Player, PlayerAdmin)

class WriterAdmin(admin.ModelAdmin):
    list_display = ('user', 'onelinebio')
admin.site.register(Writer, WriterAdmin)

class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'pool')
admin.site.register(Topic, TopicAdmin)

class PieceAdmin(admin.ModelAdmin):
    list_display = ('topic', 'frontpage', 'writer', 'text', 'new_topic', 'status', 'rejection_reason', 'rating')
admin.site.register(Piece, PieceAdmin)
