from django.db import transaction
from django.db.models import Prefetch
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .acceso import MENSAJE_PREMIUM, esta_bloqueado, premium_de_la_peticion
from .aprendizaje import registrar_actividad_educativa, resumen_progreso
from .recomendaciones import recomendaciones_para
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
        contenido = serializer.validated_data['contenido']
        if esta_bloqueado(contenido, premium_de_la_peticion(request)):
            return Response({'detail': MENSAJE_PREMIUM}, status=status.HTTP_403_FORBIDDEN)
        completado = serializer.validated_data.get('completado', True)
        antes = InteraccionContenido.objects.filter(usuario=request.user, contenido=contenido).first()
        ya_estaba_completado = bool(antes and antes.completado)
        interaccion, creada = InteraccionContenido.objects.update_or_create(
            usuario=request.user,
            contenido=contenido,
            defaults={'completado': completado},
        )
        datos = dict(self.get_serializer(interaccion).data)
        # Puntos, racha e insignias: solo la primera vez que queda completado.
        if completado and not ya_estaba_completado:
            datos['gamificacion'] = registrar_actividad_educativa(
                request.user, 'contenido_leido', contenido.id
            )
        return Response(datos, status=status.HTTP_201_CREATED if creada else status.HTTP_200_OK)


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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if esta_bloqueado(serializer.validated_data['ejercicio'], premium_de_la_peticion(request)):
            return Response({'detail': MENSAJE_PREMIUM}, status=status.HTTP_403_FORBIDDEN)
        registro = serializer.save(usuario=request.user)
        datos = dict(self.get_serializer(registro).data)
        datos['gamificacion'] = registrar_actividad_educativa(
            request.user, 'ejercicio_completado', registro.ejercicio_id
        )
        return Response(datos, status=status.HTTP_201_CREATED)


class ProgresoAprendizajeView(APIView):
    """
    GET /api/educativo/progreso/ -> puntos, nivel, racha, insignias por ruta
    e historial reciente de la usuaria autenticada.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(resumen_progreso(request.user))


class RecomendacionesView(APIView):
    """
    GET /api/educativo/recomendaciones/ -> contenidos y ejercicios ordenados
    para la usuaria, con el motivo de cada recomendación y las señales de
    Seguimiento (dolor, ánimo y ciclo de los últimos 7 días) que se usaron.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(recomendaciones_para(request.user, premium_de_la_peticion(request)))


class ChatbotEducativoView(APIView):
    """
    GET  -> Devuelve el listado de preguntas frecuentes agrupadas por categorías y organizadas para el chatbot.
    POST -> Recibe {"pregunta": "..."} o {"query": "..."}, verifica el filtro estricto de contexto (Guardrail)
            para endometriosis, salud femenina, dolor pélvico o calidad de vida. Si no cumple, responde con la
            guía establecida limpia y sin emojis.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        preguntas = PreguntaFrecuente.objects.select_related('articulo_relacionado').all()
        serializer = PreguntaFrecuenteSerializer(preguntas, many=True, context={'request': request})
        
        # Categorías organizadas para el frontend
        categorias = [
            {"id": "sintomas", "nombre": "Síntomas y Dolor", "icono": "healing"},
            {"id": "nutricion", "nombre": "Nutrición Antiinflamatoria", "icono": "restaurant"},
            {"id": "tratamientos", "nombre": "Tratamientos y Citas", "icono": "medical_services"},
            {"id": "bienestar", "nombre": "Calidad de Vida", "icono": "favorite"},
        ]

        return Response({
            'categorias': categorias,
            'preguntas_frecuentes': serializer.data
        })

    def post(self, request):
        query = request.data.get('pregunta') or request.data.get('query') or ''
        query_lower = query.strip().lower()

        todas = PreguntaFrecuente.objects.select_related('articulo_relacionado').all()
        sugeridas_serializer = PreguntaFrecuenteSerializer(todas, many=True, context={'request': request})

        # Filtro estricto de contexto (Guardrail): Validar si pertenece a endometriosis, salud femenina, dolor pélvico o calidad de vida
        keywords_validas = [
            'endometriosis', 'dolor', 'pélvico', 'pelvico', 'salud', 'femenina', 'nutrición', 'nutricion',
            'antiinflamatoria', 'tratamiento', 'citas', 'cita', 'calidad de vida', 'fatiga', 'sop',
            'miomas', 'menopausia', 'ciclo', 'menstruación', 'menstruacion', 'síntomas', 'sintomas',
            'ansiedad', 'fisioterapia', 'terapia', 'dieta', 'ejercicio', 'médico', 'medico', 'especialista'
        ]

        es_valida = any(kw in query_lower for kw in keywords_validas) or len(query_lower) < 3

        if not es_valida:
            respuesta_guardrail = (
                'Como tu asistente en Endometriosis, solo puedo responder consultas sobre la enfermedad, manejo del dolor, nutrición y tu calidad de vida. ¿Te gustaría consultar sobre alguno de estos temas?'
            )
            return Response({
                'respuesta': respuesta_guardrail,
                'articulo_relacionado': None,
                'preguntas_sugeridas': sugeridas_serializer.data,
            })

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

        match = None
        palabras = [p for p in query_lower.split() if len(p) > 2]
        
        for item in todas:
            if query_lower in item.pregunta.lower() or item.pregunta.lower() in query_lower:
                match = item
                break

        if not match and palabras:
            max_coincidentes = 0
            for item in todas:
                texto_completo = f"{item.pregunta} {item.respuesta}".lower()
                coincidentes = sum(1 for p in palabras if p in texto_completo)
                if coincidentes > max_coincidentes:
                    max_coincidentes = coincidentes
                    match = item

        if match:
            articulo_data = ContenidoEducativoSerializer(
                match.articulo_relacionado, context={'request': request}
            ).data if match.articulo_relacionado else None
            return Response({
                'respuesta': match.respuesta,
                'articulo_relacionado': articulo_data,
                'preguntas_sugeridas': sugeridas_serializer.data,
            })
        else:
            return Response({
                'respuesta': 'Como tu asistente en Endometriosis, puedo ayudarte con consultas sobre manejo del dolor, nutrición antiinflamatoria, tratamientos y calidad de vida. Por favor, selecciona una de las preguntas frecuentes o especifica tu duda sobre estos temas.',
                'articulo_relacionado': None,
                'preguntas_sugeridas': sugeridas_serializer.data,
            })
