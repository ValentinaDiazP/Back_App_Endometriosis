from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import Publicacion, Comentario, Professional
from .serializers import ProfessionalSerializer, ComentarioSerializer

class ProfessionalViewSet(viewsets.ModelViewSet):
    queryset = Professional.objects.all()
    serializer_class = ProfessionalSerializer

from rest_framework import viewsets, permissions
from .models import Publicacion, Comentario
from .serializers import PublicacionSerializer, ComentarioSerializer
class PublicacionViewSet(viewsets.ModelViewSet):
    queryset = Publicacion.objects.all()
    serializer_class = PublicacionSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        # TODO: [PENDIENTE REGISTRO]
        # Actualmente asigna None si la usuaria no se ha autenticado.
        # Cuando se implemente Auth Token, cambiar a:
        # serializer.save(usuario=self.request.user)
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(usuario=user)


class ComentarioViewSet(viewsets.ModelViewSet):
    queryset = Comentario.objects.all()
    serializer_class = ComentarioSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(usuario=user)
