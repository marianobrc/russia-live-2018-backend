from django.contrib import admin
from .models import Match, MatchEvent


class MatchAdmin(admin.ModelAdmin):
    list_filter = (
        'status',
        'is_live',
    )

class MatchEventAdmin(admin.ModelAdmin):
    list_filter = (
        'match',
        'event_type',
    )

admin.site.register(Match, MatchAdmin)
admin.site.register(MatchEvent, MatchEventAdmin)

