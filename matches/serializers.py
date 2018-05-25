from rest_framework import serializers

from teams.serializers import PlayerSerializer
from .models import Match, MatchEvent, MatchStats


class MatchSerializer(serializers.ModelSerializer):

    class Meta:
        model = Match
        fields = (
            'id', 'stage', 'stage_detail', 'date', 'stadium', 'status',
            'is_live', 'team1', 'team2', 'team1_score', 'team2_score',
        )
        depth = 2


class MatchEventSerializer(serializers.ModelSerializer):
    team = serializers.PrimaryKeyRelatedField(read_only=True)
    player = PlayerSerializer(many=False, read_only=True)

    class Meta:
        model = MatchEvent
        fields = (
            'id', 'team', 'player', 'event_type', 'minute', 'extra_minute', 'description', 'description2',
        )


class MatchStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchStats
        fields = (
            'team', 'match', 'possession',
        )


class MatchDetailSerializer(serializers.ModelSerializer):
    events = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()

    def get_events(self, obj): # Return last event first
         ordered_queryset = obj.events.all().order_by('-minute')
         return MatchEventSerializer(ordered_queryset, many=True, read_only=True, context=self.context).data

    def get_stats(self, obj): # Return last event first
         queryset = obj.match_stats.all()
         return MatchStatsSerializer(queryset, many=True, read_only=True, context=self.context).data

    class Meta:
        model = Match
        fields = (
            'id', 'stage', 'stage_detail', 'date', 'stadium', 'minutes', 'status',
            'is_live', 'team1', 'team2', 'team1_score', 'team2_score',
            'events', 'stats',
        )
        depth = 2

