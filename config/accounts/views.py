from django.shortcuts import render
from rest_framework.generics import CreateAPIView
from . import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class SignUpApiView(CreateAPIView):
  queryset = User.objects.all()
  serializer_class = serializers.SignUpSerializer

