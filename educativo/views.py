import os
import logging
from pathlib import Path
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured
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

logger = logging.getLogger(__name__)

# Cargar variables de entorno desde .env
load_dotenv()

# Intentar importar Google Genai SDK si está instalado
try:
    from google import genai
    from google.genai import types
    GENAI_DISPONIBLE = True
except ImportError:
    GENAI_DISPONIBLE = False


class RagError(Exception):
    """Excepción personalizada para errores de RAG o respuestas vacías de Gemini."""
    pass


def generar_respuesta_rag(pregunta: str) -> str:
    """
    Carga knowledge_base.md completo y consulta a Gemini 2.5 Flash con thinking_budget=0.
    Lanza ImproperlyConfigured si falta el archivo o tiene < 500 caracteres.
    Lanza RagError si la respuesta de Gemini está vacía.
    Registra cualquier excepción técnica con logger.exception y devuelve 503 en la vista.
    """
    BASE_DIR = Path(__file__).resolve().parent.parent
    kb_path = Path(__file__).resolve().parent / "knowledge_base.md"
    
    if not kb_path.exists():
        raise ImproperlyConfigured("El archivo knowledge_base.md no existe.")
    
    kb_content = kb_path.read_text(encoding="utf-8")
    if len(kb_content) < 500:
        raise ImproperlyConfigured("El archivo knowledge_base.md tiene menos de 500 caracteres.")

    load_dotenv(BASE_DIR / ".env")
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        raise ImproperlyConfigured("No se encontró GEMINI_API_KEY en el entorno.")

    client = genai.Client(api_key=gemini_api_key)
    
    system_instruction = (
        "Eres un asistente virtual educativo especializado EXCLUSIVAMENTE en endometriosis. "
        "Responde ÚNICAMENTE usando la información de <knowledge_base>.\n"
        "Reglas obligatorias:\n"
        "- Responde en texto plano, sin Markdown ni asteriscos.\n"
        "- Máximo 130 palabras.\n"
        "- Tono empático, cálido y pedagógico.\n"
        "- Termina siempre con la fuente científica exacta que aparece en el documento (ej.: 'Fuente: Guía ESHRE, 2022').\n"
        "- Prohibido diagnosticar, interpretar exámenes/ecografías, o recetar/dosificar fármacos.\n"
        "- Si la pregunta no tiene ninguna relación con el documento, responde exactamente: "
        "'No dispongo de esa información específica en mi base educacional. Te sugiero consultarlo directamente con tu equipo médico.'"
    )

    prompt = f"<knowledge_base>\n{kb_content}\n</knowledge_base>\n\nPregunta: {pregunta}"

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
                max_output_tokens=1024,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
    except Exception as e:
        logger.exception("Error al invocar la API de Gemini Flash.")
        raise RagError(f"Error técnico al generar respuesta con Gemini: {e}")

    texto_respuesta = (response.text or "").strip()
    if not texto_respuesta:
        finish_reason = getattr(response, "finish_reason", "UNKNOWN")
        raise RagError(f"Gemini devolvió una respuesta vacía. Finish reason: {finish_reason}")

    return texto_respuesta


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
    queryset = EjercicioPsicoeducativo.objects.prefetch_related('pasos_modulo', 'indicaciones')
    serializer_class = EjercicioPsicoeducativoSerializer
    permission_classes = [permissions.IsAuthenticated]


class RutaAprendizajeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RutaAprendizaje.objects.prefetch_related(
        Prefetch('pasos', queryset=RutaAprendizajeContenido.objects.select_related('contenido'))
    )
    serializer_class = RutaAprendizajeSerializer
    permission_classes = [permissions.IsAuthenticated]


class PreferenciasView(APIView):
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
        if completado and not ya_estaba_completado:
            datos['gamificacion'] = registrar_actividad_educativa(
                request.user, 'contenido_leido', contenido.id
            )
        return Response(datos, status=status.HTTP_201_CREATED if creada else status.HTTP_200_OK)


class RegistroEjercicioViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet
):
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
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(resumen_progreso(request.user))


class RecomendacionesView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(recomendaciones_para(request.user, premium_de_la_peticion(request)))


class ChatbotEducativoView(APIView):
    """
    GET  -> Devuelve las categorías y preguntas frecuentes iniciales.
    POST -> Recibe {"pregunta": "..."} o {"query": "..."}, verifica protocolos de crisis,
            separa las 3 preguntas del carrusel inferior (con tarjetas CTA exactas) de las
            25 preguntas del menú y consultas abiertas (procesadas estrictamente mediante RAG Gemini Flash + knowledge_base.md completo).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        preguntas = PreguntaFrecuente.objects.select_related('articulo_relacionado').all()
        serializer = PreguntaFrecuenteSerializer(preguntas, many=True, context={'request': request})
        
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

        # ---------------------------------------------------------------------
        # (1) FILTRO DE CRISIS
        # ---------------------------------------------------------------------
        keywords_crisis = ['suicidio', 'matar', 'morir', 'autolesión', 'autolesion', 'sangrado abundante', 'hemorragia aguda', 'fiebre alta', 'daño', 'vivir', 'respirar', 'insoportable']
        if any(c in query_lower for c in keywords_crisis):
            respuesta_crisis = (
                "⚠️ ATENCIÓN MÉDICA INMEDIATA:\n"
                "Si estás experimentando dolor extremo incapacitante, hemorragia aguda o pensamientos de autolesión, "
                "por favor acude inmediatamente a urgencias y comunícate con las líneas locales de emergencia:\n"
                "• Línea 106 / Línea 192 (Colombia)\n"
                "• O acude al centro médico más cercano de inmediato."
            )
            return Response({
                'respuesta': respuesta_crisis,
                'articulo_relacionado': None,
                'opciones_sugeridas': [
                    "1. Fisiopatología, síntomas y mecanismos del dolor",
                    "2. Salud mental y afrontamiento psicoemocional",
                    "3. Explicación de tratamientos médicos y quirúrgicos",
                    "4. Nutrición, estilo de vida y terapias complementarias",
                    "5. Autogestión del síntoma y comunicación médica"
                ],
                'preguntas_sugeridas': sugeridas_serializer.data,
            })

        # ---------------------------------------------------------------------
        # (2) NAVEGACIÓN DEL MENÚ
        # ---------------------------------------------------------------------
        if query_lower in ["volver al menú principal", "menú", "menu", "volver"]:
            temas_principales = [
                "1. Fisiopatología, síntomas y mecanismos del dolor",
                "2. Salud mental y afrontamiento psicoemocional",
                "3. Explicación de tratamientos médicos y quirúrgicos",
                "4. Nutrición, estilo de vida y terapias complementarias",
                "5. Autogestión del síntoma y comunicación médica"
            ]
            respuesta_texto = (
                "¡Hola! Soy tu asistente educativo sobre Endometriosis 🌸. Puedo orientarte de forma segura en estos 5 temas:\n"
                "1. Fisiopatología, síntomas y mecanismos del dolor\n"
                "2. Salud mental y afrontamiento psicoemocional\n"
                "3. Explicación de tratamientos médicos y quirúrgicos\n"
                "4. Nutrición, estilo de vida y terapias complementarias\n"
                "5. Autogestión del síntoma y comunicación médica\n\n"
                "Selecciona un número del 1 al 5 abajo o escribe tu duda."
            )
            return Response({
                'respuesta': respuesta_texto,
                'articulo_relacionado': None,
                'opciones_sugeridas': temas_principales,
                'preguntas_sugeridas': sugeridas_serializer.data,
            })

        temas_principales = [
            "1. Fisiopatología, síntomas y mecanismos del dolor",
            "2. Salud mental y afrontamiento psicoemocional",
            "3. Explicación de tratamientos médicos y quirúrgicos",
            "4. Nutrición, estilo de vida y terapias complementarias",
            "5. Autogestión del síntoma y comunicación médica"
        ]

        preguntas_por_tema = {
            "1": [
                "¿Qué es exactamente la endometriosis y dónde aparece el tejido?",
                "¿Por qué causa tanto dolor incluso cuando las lesiones son pequeñas?",
                "¿Qué síntomas digestivos o urinarios puede provocar la endometriosis?",
                "¿Es normal tener cólicos menstruales que impiden trabajar o estudiar?",
                "¿Por qué la endometriosis genera cansancio o fatiga persistente?"
            ],
            "2": [
                "¿Por qué la endometriosis afecta tanto el estado de ánimo y genera ansiedad?",
                "¿Qué es la catastrofización del dolor y cómo influye en cómo me siento?",
                "¿Cómo manejar el estigma cuando mi entorno minimiza mi dolor?",
                "¿Qué técnica rápida puedo usar cuando siento sobrecarga emocional por el dolor?",
                "¿Dónde encuentro ejercicios guiados de TCC, ACT o Mindfulness en la app?"
            ],
            "3": [
                "¿Los tratamientos hormonales curan la endometriosis o solo controlan los síntomas?",
                "¿Cómo actúan las progestinas (como el Dienogest) o los anticonceptivos en la endometriosis?",
                "¿Qué diferencia hay entre los analgésicos (AINEs) y el tratamiento hormonal?",
                "¿Qué son los antagonistas o análogos de GnRH y cuándo se consideran?",
                "¿Cuál es la diferencia entre escisión laparoscópica y ablación en una cirugía?"
            ],
            "4": [
                "¿Qué patrón de alimentación respalda la ciencia para apoyar el manejo inflamatorio?",
                "¿Por qué se recomienda la fisioterapia de suelo pélvico en la endometriosis?",
                "¿Qué tipo de ejercicio físico es más seguro cuando tengo dolor pélvico crónico?",
                "¿Qué medidas inmediatas ayudan durante un brote (flare-up) de dolor agudo?",
                "¿Es necesario eliminar el gluten o los lácteos si tengo endometriosis?"
            ],
            "5": [
                "¿Qué datos diarios conviene registrar para entender mejor mis síntomas?",
                "¿Cómo puedo preparar mi consulta médica para que mi dolor sea escuchado?",
                "¿Qué preguntas clave debo hacerle a mi ginecólogo sobre mi plan de manejo?",
                "¿Cómo me ayuda el resumen PDF de la sección Reportes en mi cita médica?",
                "¿Qué significa la toma de decisiones compartida en el tratamiento de la endometriosis?"
            ]
        }

        for num in ["1", "2", "3", "4", "5"]:
            if query_lower == num or query_lower.startswith(f"{num}.") or query_lower.startswith(f"tema {num}"):
                tema_titulo = temas_principales[int(num) - 1]
                subpreguntas = preguntas_por_tema[num]
                respuesta_texto = (
                    f"Has seleccionado el tema {num}: {tema_titulo.split('. ', 1)[1]}.\n\n"
                    "Selecciona una de las siguientes preguntas para explorar en profundidad o escribe tu duda:"
                )
                return Response({
                    'respuesta': respuesta_texto,
                    'articulo_relacionado': None,
                    'opciones_sugeridas': subpreguntas + ["Volver al menú principal"],
                    'preguntas_sugeridas': sugeridas_serializer.data,
                })

        # ---------------------------------------------------------------------
        # (3) CARRUSEL INFERIOR (3 PREGUNTAS RÁPIDAS)
        # ---------------------------------------------------------------------
        carrusel_p1 = "¿cómo gestionar la ansiedad o el impacto emocional del diagnóstico?"
        carrusel_p2 = "¿cómo puedo manejar la fatiga crónica asociada a la endometriosis?"
        carrusel_p3 = "¿qué puedo hacer durante un brote (flare-up) de dolor agudo?"

        if query_lower == carrusel_p1 or query_lower == carrusel_p2:
            art = ContenidoEducativo.objects.filter(titulo__icontains="más allá del dolor físico").first() or \
                  ContenidoEducativo.objects.filter(titulo__icontains="más allá del dolor").first() or \
                  ContenidoEducativo.objects.first()
            art_data = ContenidoEducativoSerializer(art, context={'request': request}).data if art else None
            
            if query_lower == carrusel_p1:
                resp_carrusel = (
                    "El impacto emocional del diagnóstico de endometriosis es profundo y real. La incertidumbre y el dolor "
                    "generan estrés y ansiedad sostenida. Practicar la aceptación sin lucha y contar con apoyo psicológico "
                    "ayuda a sobrellevarlo de forma saludable.\n\nFuente: del Pino-Sedeño et al., 2024; Donatti et al., 2022."
                )
            else:
                resp_carrusel = (
                    "La fatiga crónica en la endometriosis es un síntoma sistémico derivado de la inflamación crónica, la alteración "
                    "del sueño y el desgaste físico constante. Requiere pacing (distribución equilibrada de energía), descanso consciente y apoyo integral.\n\nFuente: ESHRE Guideline, 2022; OMS."
                )

            return Response({
                'respuesta': resp_carrusel,
                'articulo_relacionado': art_data,
                'opciones_sugeridas': ["Volver al menú principal"],
                'preguntas_sugeridas': sugeridas_serializer.data,
            })

        if query_lower == carrusel_p3:
            art = ContenidoEducativo.objects.filter(titulo__icontains="entendiendo el dolor crónico").first() or \
                  ContenidoEducativo.objects.filter(titulo__icontains="dolor crónico").first() or \
                  ContenidoEducativo.objects.first()
            art_data = ContenidoEducativoSerializer(art, context={'request': request}).data if art else None
            return Response({
                'respuesta': (
                    "Durante un brote (flare-up) agudo, aplica calor local moderado, descansa en una postura cómoda, "
                    "realiza respiración diafragmática lenta para calmar el sistema nervioso y utiliza tus analgésicos o pautas médicas indicadas. "
                    "Acude a urgencias si el dolor es insoportable o inusual.\n\nFuente: ACOG Practice Bulletin, 2010; ESHRE, 2022."
                ),
                'articulo_relacionado': art_data,
                'opciones_sugeridas': ["Volver al menú principal"],
                'preguntas_sugeridas': sugeridas_serializer.data,
            })

        # ---------------------------------------------------------------------
        # (4) CONSULTAS RAG (25 SUBPREGUNTAS O TEXTO LIBRE)
        # ---------------------------------------------------------------------
        try:
            respuesta_rag = generar_respuesta_rag(query)
        except (ImproperlyConfigured, RagError):
            return Response(
                {"detail": "Error interno en el servicio de chatbot educativo."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        return Response({
            'respuesta': respuesta_rag,
            'articulo_relacionado': None,
            'opciones_sugeridas': ["Volver al menú principal"],
            'preguntas_sugeridas': sugeridas_serializer.data,
        })
