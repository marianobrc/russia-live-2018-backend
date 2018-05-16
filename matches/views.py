from rest_framework.generics import ListAPIView, RetrieveAPIView
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter
from .serializers import MatchSerializer, MatchDetailSerializer
from .models import Match


class MatchesListAPIView(ListAPIView):
    queryset = Match.objects.all()
    serializer_class = MatchSerializer
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter,)
    filter_fields = ('is_live', 'status', 'date', 'id', 'stage', 'stage__name', )
    ordering_fields = ('date', 'id', )


class MatchDetailsAPIView(RetrieveAPIView):
    queryset = Match.objects.all()
    serializer_class = MatchDetailSerializer

