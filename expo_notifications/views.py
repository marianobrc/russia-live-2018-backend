from django.shortcuts import render
from rest_framework import generics

from expo_notifications.models import PushToken
from .serializers import PushTokenSerializer


class PushTokenCreateAPIView(generics.CreateAPIView):
    serializer_class = PushTokenSerializer


class PushSettingsRetrieveUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = PushToken.objects.all()
    serializer_class = PushTokenSerializer
    lookup_field = 'token'
