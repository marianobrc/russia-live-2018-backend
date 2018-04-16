from django.shortcuts import render
from rest_framework.generics import ListAPIView
from django_filters import rest_framework as filters
from .serializers import MatchSerializer
from .models import Match


class MatchesListAPIView(ListAPIView):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('is_live', 'status',)

