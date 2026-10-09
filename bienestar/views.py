from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from sintomas.gamificacion import registrar_actividad
from .models import Publicacion, Comentario, Professional, MeGusta, ReportePublicacion, SolicitudContacto
from .serializers import (
    PublicacionSerializer,
    ComentarioSerializer,
    ProfessionalSerializer,
    SolicitudContactoSerializer,
)


class ProfessionalViewSet(viewsets.ModelViewSet):
    queryset = Professional.objects.all()
    serializer_class = ProfessionalSerializer
    permission_classes = [permissions.AllowAny]


class PublicacionViewSet(viewsets.ModelViewSet):
    serializer_class = PublicacionSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return Publicacion.objects.filter(estado='APROBADO').order_by('-fecha_creacion')

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(usuario=user, estado='APROBADO')
        if user is not None:
            registrar_actividad(user, 'comunidad_post')

    @action(detail=True, methods=['post'])
    def reaccionar(self, request, pk=None):
        publicacion = self.get_object()
        usuario = request.user

        if not usuario.is_authenticated:
            return Response(
                {'error': 'Debes iniciar sesión para dar me gusta'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        megusta, created = MeGusta.objects.get_or_create(publicacion=publicacion, usuario=usuario)

        if not created:
            megusta.delete()
            return Response({'status': 'Like eliminado', 'me_gusta': False}, status=status.HTTP_200_OK)

        return Response({'status': 'Like agregado', 'me_gusta': True}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def comentar(self, request, pk=None):
        publicacion = self.get_object()
        user = request.user if request.user.is_authenticated else None
        texto = request.data.get('texto', '').strip()

        if not texto:
            return Response(
                {'error': 'El comentario no puede estar vacío.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        comentario = Comentario.objects.create(publicacion=publicacion, usuario=user, texto=texto)
        if user is not None:
            registrar_actividad(user, 'comunidad_comentario')
        serializer = ComentarioSerializer(comentario)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def reportar(self, request, pk=None):
        publicacion = self.get_object()
        motivo = request.data.get('motivo', '')

        if not request.user.is_authenticated:
            return Response(
                {'error': 'Debes iniciar sesión para reportar una publicación'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        ReportePublicacion.objects.create(
            publicacion=publicacion,
            usuario=request.user,
            motivo=motivo,
        )

        publicacion.estado = 'PENDIENTE'
        publicacion.save()

        return Response(
            {'status': 'Publicación reportada y enviada a revisión'},
            status=status.HTTP_200_OK,
        )


class ComentarioViewSet(viewsets.ModelViewSet):
    queryset = Comentario.objects.all()
    serializer_class = ComentarioSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(usuario=user)
        if user is not None:
            registrar_actividad(user, 'comunidad_comentario')


class SolicitudContactoViewSet(viewsets.ModelViewSet):
    serializer_class = SolicitudContactoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SolicitudContacto.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user, estado='PENDIENTE')
