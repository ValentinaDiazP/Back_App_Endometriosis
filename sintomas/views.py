from rest_framework import permissions, viewsets

from .models import LocalizacionDolor, RegistroSintoma, SintomaAsociado
from .serializers import (
    LocalizacionDolorSerializer,
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