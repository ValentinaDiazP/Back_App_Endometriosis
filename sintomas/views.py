from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import LocalizacionDolor, RegistroEmocional, RegistroSintoma, SintomaAsociado
from .serializers import (
    LocalizacionDolorSerializer,
    RegistroEmocionalSerializer,
    RegistroSintomaSerializer,
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
        from datetime import date
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
            return Response(serializer.data, status=status.HTTP_200_OK)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(usuario=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], url_path='hoy')
    def hoy(self, request):
        """GET /api/sintomas/registros-emocionales/hoy/ — devuelve el
        registro de hoy si existe, o 204 (sin contenido) si no."""
        from datetime import date
        registro = RegistroEmocional.objects.filter(
            usuario=request.user, fecha=date.today()
        ).first()
        if registro is None:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(self.get_serializer(registro).data)