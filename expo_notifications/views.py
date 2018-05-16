from django.shortcuts import render
from rest_framework import generics
from .serializers import PushTokenSerializer

class PushTokenCreateAPIView(generics.CreateAPIView):
    serializer_class = PushTokenSerializer
