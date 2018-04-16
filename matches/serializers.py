from rest_framework import serializers
from .models import Match, MatchEvent


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

    class Meta:
        model = MatchEvent
        fields = (
            'id', 'team', 'player', 'event_type', 'minute', 'extra_minute', 'description'
        )


class MatchDetailSerializer(serializers.ModelSerializer):
    events = MatchEventSerializer(many=True, read_only=True)

    class Meta:
        model = Match
        fields = (
            'id', 'stage', 'stage_detail', 'date', 'stadium', 'status',
            'is_live', 'team1', 'team2', 'team1_score', 'team2_score',
            'events',
        )
        depth = 2

