from django.shortcuts import render
from rest_framework.generics import ListAPIView
from .serializers import MatchSerializer
from .models import Match


class MatchesListAPIView(ListAPIView):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
