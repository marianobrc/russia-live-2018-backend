from rest_framework import serializers
from .models import Match


class MatchSerializer(serializers.ModelSerializer):

    class Meta:
        model = Match
        fields = (
            'id', 'stage', 'stage_detail', 'date', 'stadium', 'status',
            'is_live', 'team1', 'team2', 'team1_score', 'team2_score',
        )
        depth = 2

