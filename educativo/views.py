from django.db import transaction
from django.db.models import Prefetch
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    CategoriaContenido,
    ContenidoEducativo,
    EjercicioPsicoeducativo,
    InteraccionContenido,
    PreferenciaUsuario,
    RegistroEjercicio,
    RutaAprendizaje,
    RutaAprendizajeContenido,
)
from .serializers import (
    CategoriaContenidoSerializer,
    ContenidoEducativoSerializer,
    EjercicioPsicoeducativoSerializer,
    InteraccionContenidoSerializer,
    PreferenciasSerializer,
    RegistroEjercicioSerializer,
    RutaAprendizajeSerializer,
)


# Todo el catálogo es de solo lectura desde la app: el contenido se carga y
# edita desde el admin de Django.


class CategoriaContenidoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CategoriaContenido.objects.all()
    serializer_class = CategoriaContenidoSerializer
    permission_classes = [permissions.IsAuthenticated]


class ContenidoEducativoViewSet(viewsets.ReadOnlyModelViewSet):
    """Admite filtrar por categoría: ?categoria=cat_dolor"""
    serializer_class = ContenidoEducativoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = ContenidoEducativo.objects.all()
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria_id=categoria)
        return queryset


class EjercicioPsicoeducativoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EjercicioPsicoeducativo.objects.all()
    serializer_class = EjercicioPsicoeducativoSerializer
    permission_classes = [permissions.IsAuthenticated]


class RutaAprendizajeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RutaAprendizaje.objects.prefetch_related(
        Prefetch('pasos', queryset=RutaAprendizajeContenido.objects.select_related('contenido'))
    )
    serializer_class = RutaAprendizajeSerializer
    permission_classes = [permissions.IsAuthenticated]


# ---------------------------------------------------------------------------
# Datos de la usuaria autenticada. Nunca se recibe el id de usuaria desde el
# frontend: todo se filtra y se guarda con request.user.
# ---------------------------------------------------------------------------


class PreferenciasView(APIView):
    """
    GET  -> {"categorias": ["cat_dolor", ...]}
    PUT  -> reemplaza la lista completa con la que se envía.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        ids = PreferenciaUsuario.objects.filter(usuario=request.user).values_list('categoria_id', flat=True)
        return Response({'categorias': list(ids)})

    def put(self, request):
        serializer = PreferenciasSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ids = serializer.validated_data['categorias']
        with transaction.atomic():
            PreferenciaUsuario.objects.filter(usuario=request.user).delete()
            PreferenciaUsuario.objects.bulk_create(
                PreferenciaUsuario(usuario=request.user, categoria_id=i) for i in ids
            )
        return Response({'categorias': ids})


class InteraccionContenidoViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    """
    GET  -> interacciones de la usuaria.
    POST {"contenido": "c1"} -> marca el contenido como completado. Si ya
    existía la interacción, la actualiza en lugar de duplicarla.
    """
    serializer_class = InteraccionContenidoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return InteraccionContenido.objects.filter(usuario=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        interaccion, creada = InteraccionContenido.objects.update_or_create(
            usuario=request.user,
            contenido=serializer.validated_data['contenido'],
            defaults={'completado': serializer.validated_data.get('completado', True)},
        )
        return Response(
            self.get_serializer(interaccion).data,
            status=status.HTTP_201_CREATED if creada else status.HTTP_200_OK,
        )


class RegistroEjercicioViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
    """
    GET  -> registros de la usuaria.
    POST {"ejercicio": "e1", "respuestas": "...", "utilidad": 4} -> nuevo
    registro (respuestas y utilidad son opcionales).
    """
    serializer_class = RegistroEjercicioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RegistroEjercicio.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
