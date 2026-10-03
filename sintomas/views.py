from datetime import date, timedelta

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .gamificacion import registrar_actividad
from .models import (
    Gamificacion,
    LocalizacionDolor,
    MovimientoPuntos,
    NivelGamificacion,
    RegistroEmocional,
    RegistroSintoma,
    SintomaAsociado,
    RegistroCiclo,
)
from .serializers import (
    LocalizacionDolorSerializer,
    RegistroEmocionalSerializer,
    RegistroSintomaSerializer,
    RegistroCicloSerializer,
    SintomaAsociadoSerializer,
)

class LocalizacionDolorViewSet(viewsets.ReadOnlyModelViewSet):
    """Catálogo de solo lectura — nadie crea zonas de dolor desde la app."""
    queryset = LocalizacionDolor.objects.all()
    serializer_class = LocalizacionDolorSerializer
    permission_classes = [permissions.IsAuthenticated]


class SintomaAsociadoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SintomaAsociado.objects.all()
    serializer_class = SintomaAsociadoSerializer
    permission_classes = [permissions.IsAuthenticated]


class RegistroSintomaViewSet(viewsets.ModelViewSet):
    """
    CRUD completo, pero cada usuaria solo ve y modifica sus propios
    registros (filtrado en get_queryset, nunca se recibe el id de usuaria
    desde el frontend).
    """
    serializer_class = RegistroSintomaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RegistroSintoma.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
        registrar_actividad(self.request.user, 'registro_sintoma')
class RegistroEmocionalViewSet(viewsets.ModelViewSet):
    """
    CRUD del check-in emocional, con la regla especial de "un solo
    registro por día": en vez de un simple perform_create, create()
    hace upsert (actualiza si ya existe el de hoy, crea si no).
    """
    serializer_class = RegistroEmocionalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RegistroEmocional.objects.filter(usuario=self.request.user)

    def create(self, request, *args, **kwargs):
        hoy = date.today()
        registro_existente = RegistroEmocional.objects.filter(
            usuario=request.user, fecha=hoy
        ).first()

        if registro_existente:
            serializer = self.get_serializer(
                registro_existente, data=request.data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            registrar_actividad(request.user, 'checkin_emocional')
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(usuario=request.user)
        registrar_actividad(request.user, 'checkin_emocional')
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='hoy')
    def hoy(self, request):
        """GET /api/sintomas/registros-emocionales/hoy/ — devuelve el
        registro de hoy si existe, o 204 (sin contenido) si no."""
        registro = RegistroEmocional.objects.filter(
            usuario=request.user, fecha=date.today()
        ).first()
        if registro is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(self.get_serializer(registro).data)

class RegistroCicloViewSet(viewsets.ModelViewSet):
    """
    CRUD de ciclos. Cada usuaria solo ve y modifica los suyos. Los puntos
    se dan solo al crear (no al editar), para que editar un ciclo no sirva
    para acumular puntos.
    """
    serializer_class = RegistroCicloSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return RegistroCiclo.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user)
        registrar_actividad(self.request.user, 'registro_ciclo')

class GamificacionView(APIView):
    """GET /api/sintomas/gamificacion/: puntos, racha, nivel e historial."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        hoy = date.today()
        gami, _ = Gamificacion.objects.get_or_create(usuario=request.user)

        # Si se saltó un día, la racha guardada ya no está vigente.
        racha = gami.racha_actual
        if gami.ultimo_dia_activo is None or gami.ultimo_dia_activo < hoy - timedelta(days=1):
            racha = 0

        nivel = None
        siguiente = None
        for n in NivelGamificacion.objects.all():
            if n.puntos_minimos <= gami.puntos_totales:
                nivel = n
            else:
                siguiente = n
                break

        historial = MovimientoPuntos.objects.filter(usuario=request.user)[:30]

        return Response({
            'puntos_totales': gami.puntos_totales,
            'racha_actual': racha,
            'racha_maxima': gami.racha_maxima,
            'nivel': {'nombre': nivel.nombre, 'puntos_minimos': nivel.puntos_minimos} if nivel else None,
            'siguiente_nivel': {'nombre': siguiente.nombre, 'puntos_minimos': siguiente.puntos_minimos} if siguiente else None,
            'historial': [
                {'fecha': m.fecha, 'motivo': m.motivo, 'puntos': m.puntos}
                for m in historial
            ],
        })
    