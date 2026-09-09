from django.shortcuts import render
from rest_framework import viewsets
from .models import Professional
from .serializers import ProfessionalSerializer

class ProfessionalViewSet(viewsets.ModelViewSet):
    queryset = Professional.objects.all()
    serializer_class = ProfessionalSerializer
