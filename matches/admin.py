from django.contrib import admin
from .models import Match, MatchEvent, MatchStats


class MatchAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'stage', 'stage_detail', 'date', 'stadium', 'status',
        'is_live', 'team1', 'team2', 'team1_score', 'team2_score',
        'is_penalty_definition', 'team1_penalties_score', 'team2_penalties_score',
        'team1_lineup', 'team2_lineup', 'is_history',
    )
    list_filter = (
        'status',
        'is_live',
        'is_history',
        'stage',
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
