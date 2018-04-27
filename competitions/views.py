from rest_framework.generics import ListAPIView, RetrieveAPIView
from django_filters import rest_framework as filters
from rest_framework.filters import OrderingFilter
from .serializers import StandingSerializer
from .models import Standing


class StandingsListAPIView(ListAPIView):
    queryset = Standing.objects.all()
    serializer_class = StandingSerializer
    filter_backends = (filters.DjangoFilterBackend, OrderingFilter,)
    filter_fields = ('stage__name', 'sub_group', 'team', )
    ordering_fields = ('position', )
