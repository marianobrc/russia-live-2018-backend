from django.contrib import admin
from .models import Match, MatchEvent, MatchStats


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


class MatchStatsAdmin(admin.ModelAdmin):
    list_display = (
        'match', 'team', 'possession', 'passes', 'passes_accuracy', 'shots_total', 'shots_ongoal', 'shots_accuracy',
        'dangerous_attacks', 'courner_kicks', 'free_kicks', 'yellow_cards', 'red_cards', 'substitutions', 'fouls',
    )
    list_filter = (
        'match',
        'team',
    )


admin.site.register(Match, MatchAdmin)
admin.site.register(MatchEvent, MatchEventAdmin)
admin.site.register(MatchStats, MatchStatsAdmin)
