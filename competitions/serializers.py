from rest_framework import serializers
from .models import Standing


class StandingSerializer(serializers.ModelSerializer):

    class Meta:
        model = Standing
        fields = (
            'id', 'stage', 'sub_group', 'team', 'position',
            'played', 'won', 'drawn', 'lost', 'goal_difference', 'points', 'is_playing',
        )
        depth = 2

