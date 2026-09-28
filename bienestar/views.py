from django.shortcuts import render
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Publicacion, Comentario, Professional, MeGusta, ReportePublicacion
from .serializers import (
    PublicacionSerializer, 
    ComentarioSerializer, 
    ProfessionalSerializer
)


class ProfessionalViewSet(viewsets.ModelViewSet):
    queryset = Professional.objects.all()
    serializer_class = ProfessionalSerializer
    permission_classes = [permissions.AllowAny]


class PublicacionViewSet(viewsets.ModelViewSet):
    serializer_class = PublicacionSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        # En la app móvil solo se muestran publicaciones APROBADAS
        return Publicacion.objects.filter(estado='APROBADO').order_by('-fecha_creacion')

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        # Toda nueva publicación se crea con estado PENDIENTE hasta revisión en el admin web
        serializer.save(usuario=user, estado='PENDIENTE')

    @action(detail=True, methods=['post'])
    def reaccionar(self, request, pk=None):
        publicacion = self.get_object()
        usuario = request.user

        if not usuario.is_authenticated:
            return Response({'error': 'Usuario no autenticado'}, status=status.HTTP_401_UNAUTHORIZED)

        # Si ya existe el like, lo quita. Si no existe, lo crea.
        megusta, created = MeGusta.objects.get_or_create(publicacion=publicacion, usuario=usuario)
        
        if not created:
            megusta.delete()
            return Response({'status': 'Like eliminado', 'me_gusta': False})
        
        return Response({'status': 'Like agregado', 'me_gusta': True})
    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def comentar(self, request, pk=None):
        publicacion = self.get_object()
        user = request.user if request.user.is_authenticated else None
        texto = request.data.get('texto', '').strip()
        
        if not texto:
            return Response({'error': 'El comentario no puede estar vacío.'}, status=status.HTTP_400_BAD_REQUEST)
            
        comentario = Comentario.objects.create(publicacion=publicacion, usuario=user, texto=texto)
        serializer = ComentarioSerializer(comentario)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def reportar(self, request, pk=None):
        publicacion = self.get_object()
        motivo = request.data.get('motivo', '')

        # 1. Registra el reporte en la BD
        ReportePublicacion.objects.create(
            publicacion=publicacion,
            usuario=request.user if request.user.is_authenticated else None,
            motivo=motivo
        )

        # 2. Oculta la publicación de la app pasando su estado a PENDIENTE
        publicacion.estado = 'PENDIENTE'
        publicacion.save()

        return Response({'status': 'Publicación reportada y enviada a revisión'}, status=status.HTTP_201_CREATED)

class ComentarioViewSet(viewsets.ModelViewSet):
    queryset = Comentario.objects.all()
    serializer_class = ComentarioSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(usuario=user)