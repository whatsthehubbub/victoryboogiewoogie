from django.contrib import admin
from boogie.models import *

class PlayerAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
admin.site.register(Player, PlayerAdmin)

class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'pool')
admin.site.register(Topic, TopicAdmin)

class PieceAdmin(admin.ModelAdmin):
    list_display = ('topic', 'writer', 'text', 'new_topic', 'status', 'rejection_reason', 'rating')
admin.site.register(Piece, PieceAdmin)