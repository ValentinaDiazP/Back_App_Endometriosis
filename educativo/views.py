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
    PreguntaFrecuente,
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
    PreguntaFrecuenteSerializer,
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


class ChatbotEducativoView(APIView):
    """
    GET  -> Devuelve el listado de preguntas frecuentes disponibles para los chips/sugerencias.
    POST -> Recibe {"pregunta": "..."} o {"query": "..."}, busca coincidencias por palabras clave
            en la BD y devuelve la mejor respuesta, preguntas sugeridas y el artículo vinculado.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        preguntas = PreguntaFrecuente.objects.select_related('articulo_relacionado').all()
        serializer = PreguntaFrecuenteSerializer(preguntas, many=True)
        return Response({'preguntas_frecuentes': serializer.data})

    def post(self, request):
        query = request.data.get('pregunta') or request.data.get('query') or ''
        query_lower = query.strip().lower()

        todas = PreguntaFrecuente.objects.select_related('articulo_relacionado').all()
        sugeridas_serializer = PreguntaFrecuenteSerializer(todas, many=True)

        palabras_clave_general = ['tema', 'temas', 'opciones', 'ayuda', 'menu', 'menú', 'que tienes', 'qué tienes', 'categorias', 'categorías']
        es_general = any(k in query_lower for k in palabras_clave_general)

        if not query_lower or es_general:
            respuesta_texto = (
                'Los temas disponibles para mujeres diagnosticadas son:\n\n'
                '1. Manejo del dolor y brotes\n'
                '2. Nutrición antiinflamatoria\n'
                '3. Fatiga crónica\n'
                '4. Fisioterapia pélvica\n'
                '5. Salud emocional'
            )
            return Response({
                'respuesta': respuesta_texto,
                'articulo_relacionado': None,
                'preguntas_sugeridas': sugeridas_serializer.data,
            })

        # Búsqueda simple por coincidencia de palabras clave o subcadenas
        match = None
        palabras = [p for p in query_lower.split() if len(p) > 2]
        
        # 1. Búsqueda exacta o por subcadena en la pregunta
        for item in todas:
            if query_lower in item.pregunta.lower() or item.pregunta.lower() in query_lower:
                match = item
                break

        # 2. Búsqueda por palabras clave si no hay coincidencia exacta de subcadena
        if not match and palabras:
            max_coincidentes = 0
            for item in todas:
                texto_completo = f"{item.pregunta} {item.respuesta}".lower()
                coincidentes = sum(1 for p in palabras if p in texto_completo)
                if coincidentes > max_coincidentes:
                    max_coincidentes = coincidentes
                    match = item

        if match:
            articulo_data = ContenidoEducativoSerializer(match.articulo_relacionado).data if match.articulo_relacionado else None
            return Response({
                'respuesta': match.respuesta,
                'articulo_relacionado': articulo_data,
                'preguntas_sugeridas': sugeridas_serializer.data,
            })
        else:
            return Response({
                'respuesta': 'No he encontrado una respuesta exacta en mi base de conocimiento sobre endometriosis para tu consulta. Te sugiero revisar las preguntas frecuentes o explorar nuestros módulos educativos y de fisioterapia pélvica.',
                'articulo_relacionado': None,
                'preguntas_sugeridas': sugeridas_serializer.data,
            })
