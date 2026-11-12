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


FRASE_RECHAZO = (
    "Esa consulta está fuera de lo que puedo orientar aquí. Soy el asistente de Florecer para "
    "endometriosis y para cómo te afecta física y emocionalmente. Si es algo de salud, "
    "consúltalo con tu equipo médico."
)

SYSTEM_PROMPT_RAG = (
    "Eres el asistente educativo de Florecer, una app para mujeres con endometriosis. "
    "Acompañas con calidez y claridad.\n\n"
    "ALCANCE (decídelo tú según el sentido de la pregunta, no por palabras clave):\n"
    "- SÍ respondes: endometriosis (causas, síntomas, dolor, fatiga, tratamientos, cirugía, "
    "nutrición, ejercicio, autogestión, citas médicas, uso de la app) y todo lo que viva con ella: "
    "ánimo, ansiedad, tristeza, estrés, estigma, relaciones, sueño, sexualidad y fertilidad en relación "
    "con la endometriosis, y salud mental en ese contexto. Preguntas personales o emocionales de "
    "una mujer que convive con endometriosis también entran.\n"
    "- NO respondes: otras enfermedades o condiciones que no sean endometriosis (por ejemplo diabetes, "
    "cáncer, gripe), ni temas ajenos a la salud (geografía, tareas, programación, etc.). En esos casos "
    "responde SOLO con esta frase exacta y nada más: "
    f"'{FRASE_RECHAZO}'\n"
    "- Si una condición asociada (p. ej. depresión, ansiedad, SOP) aparece en relación con la "
    "endometriosis, respóndela solo en esa relación.\n\n"
    "CÓMO RESPONDER:\n"
    "1. Usa <knowledge_base> como fuente de hechos. Cada bloque empieza con '### ' y puede terminar con una "
    "línea 'FUENTE: ...'.\n"
    "2. Si hay un bloque que responde la pregunta, apóyate en él y termina con la línea FUENTE de ESE bloque, "
    "copiada tal cual, precedida de 'Fuente: '. Nunca cites una fuente que no esté en el bloque que usaste, "
    "ni de tu conocimiento previo, ni el título del documento.\n"
    "3. Si ningún bloque cubre la pregunta pero está dentro del alcance (p. ej. una duda personal o emocional), "
    "responde con orientación general breve, empática y prudente, SIN citar fuentes y SIN afirmar datos "
    "médicos concretos; cierra con: 'Para más detalle, consúltalo con tu equipo médico.'\n"
    "4. Si la cobertura es parcial, responde solo lo que el bloque sustenta y cierra con la misma frase. "
    "Nunca mezcles una respuesta con la frase de rechazo.\n"
    "5. Texto plano, sin Markdown ni asteriscos ni listas con símbolos. Máximo 130 palabras. Español, tono "
    "cálido, sin juzgar.\n"
    "6. Prohibido diagnosticar, interpretar exámenes o imágenes, y recetar o dosificar medicamentos. "
    "Explicar cómo funciona un tipo de tratamiento sí está permitido.\n"
    "7. Si la usuaria expresa mucho malestar emocional, valida lo que siente y sugiere buscar apoyo "
    "profesional (la sección Profesionales de la app)."
)


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
    
    system_instruction = SYSTEM_PROMPT_RAG

    prompt = f"<knowledge_base>\n{kb_content}\n</knowledge_base>\n\nPregunta de la usuaria: {pregunta}"

    try:
        response = client.models.generate_content(
            model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
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


# -----------------------------------------------------------------------------
# Respaldo sin IA: si Gemini no está disponible (falta GEMINI_API_KEY, sin red,
# cuota agotada...), se responde con el bloque de knowledge_base.md que más se
# parece a la pregunta, en vez de devolver un error a la usuaria.
# -----------------------------------------------------------------------------
MENSAJE_SIN_COINCIDENCIA = (
    "En este momento no puedo darte una respuesta personalizada a esa pregunta. "
    "Puedes explorar los temas del menú o escribir tu duda con otras palabras. "
    "Para más detalle, consúltalo con tu equipo médico."
)

_PALABRAS_VACIAS = {
    "como", "cómo", "para", "porque", "por", "que", "qué", "cual", "cuál", "cuando", "cuándo",
    "donde", "dónde", "tengo", "tiene", "tener", "esta", "este", "estoy", "puedo", "puede",
    "hacer", "mucho", "mucha", "muy", "mas", "más", "sobre", "entre", "desde", "hasta", "algo",
    "cosas", "siento", "sentir", "endometriosis", "asociada", "asociado", "durante", "debo",
}


def _raiz(palabra: str) -> str:
    """Raíz muy simple (primeras 5 letras) para que 'crónico' y 'crónica' coincidan."""
    return palabra[:5]


def _palabras_clave(texto: str) -> set:
    import re
    limpio = _normalizar_texto(texto)
    vacias = {_normalizar_texto(p) for p in _PALABRAS_VACIAS}
    return {_raiz(p) for p in re.findall(r"[a-zñ]+", limpio) if len(p) >= 4 and p not in vacias}


def _cargar_bloques_kb() -> list:
    kb_path = Path(__file__).resolve().parent / "knowledge_base.md"
    bloques, actual = [], None
    for linea in kb_path.read_text(encoding="utf-8").splitlines():
        if linea.startswith("### "):
            titulo = linea[4:].split("|", 1)[-1].strip()
            actual = {"titulo": titulo, "cuerpo": [], "fuente": None}
            bloques.append(actual)
        elif actual is not None:
            if linea.startswith("FUENTE:"):
                actual["fuente"] = linea[len("FUENTE:"):].strip()
            elif linea.startswith("## "):
                actual = None
            elif linea.strip():
                actual["cuerpo"].append(linea.strip())
    return bloques


def respuesta_local_kb(pregunta: str) -> str:
    """Devuelve el bloque de la base de conocimiento más parecido a la pregunta."""
    claves = _palabras_clave(pregunta)
    mejor, mejor_puntaje = None, 0
    for bloque in _cargar_bloques_kb():
        en_titulo = len(claves & _palabras_clave(bloque["titulo"]))
        en_cuerpo = len(claves & _palabras_clave(" ".join(bloque["cuerpo"])))
        puntaje = en_titulo * 3 + en_cuerpo
        if puntaje > mejor_puntaje:
            mejor, mejor_puntaje = bloque, puntaje
    if not mejor or mejor_puntaje < 2:
        return MENSAJE_SIN_COINCIDENCIA
    texto = " ".join(mejor["cuerpo"])
    if mejor["fuente"]:
        return f"{texto}\n\nFuente: {mejor['fuente']}"
    return f"{texto}\n\nPara más detalle, consúltalo con tu equipo médico."


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


def _normalizar_texto(texto: str) -> str:
    """Minúsculas y sin tildes, para comparar frases."""
    import unicodedata
    texto = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in texto if unicodedata.category(c) != "Mn")


# Frases (ya sin tildes) que indican riesgo emocional o autolesión.
FRASES_CRISIS_EMOCIONAL = [
    "suicid", "quitarme la vida", "quitarse la vida", "acabar con mi vida", "terminar con mi vida",
    "no quiero vivir", "ya no quiero vivir", "no quiero seguir viviendo", "quiero morir",
    "quiero morirme", "me quiero morir", "quisiera morir", "quisiera no despertar",
    "mejor muerta", "matarme", "autolesion","hacerme dano", "lastimarme",
    "cortarme las venas", "cortarme", "no vale la pena vivir", "no aguanto mas vivir",
]

# Frases (ya sin tildes) que indican urgencia física aguda.
FRASES_URGENCIA_FISICA = [
    "sangrado abundante", "sangrado muy abundante", "hemorragia", "me desangro", "desmay",
    "perdi el conocimiento", "fiebre alta", "no puedo respirar", "dificultad para respirar",
    "me falta el aire", "dolor insoportable", "dolor extremo", "dolor muy fuerte y no cede",
]

TEMAS_PRINCIPALES = [
    "1. Fisiopatología, síntomas y mecanismos del dolor",
    "2. Salud mental y afrontamiento psicoemocional",
    "3. Explicación de tratamientos médicos y quirúrgicos",
    "4. Nutrición, estilo de vida y terapias complementarias",
    "5. Autogestión del síntoma y comunicación médica",
]

MENSAJE_CRISIS_EMOCIONAL = (
    "Siento mucho que estés pasando por esto. Lo que sientes importa y no tienes que cargarlo sola.\n\n"
    "Si estás pensando en hacerte daño o en quitarte la vida, por favor habla ahora con alguien:\n"
    "• Línea 106 (salud mental, gratuita, 24 horas en Colombia)\n"
    "• Si estás en peligro inmediato, llama al 123 o ve a urgencias.\n\n"
    "Si puedes, avisa a una persona de confianza que esté contigo."
)

MENSAJE_URGENCIA_FISICA = (
    "⚠️ Lo que describes puede necesitar atención médica urgente.\n\n"
    "Acude ahora a urgencias o llama al 123 (línea de emergencias en Colombia), "
    "sobre todo si hay sangrado abundante, desmayo, fiebre alta, dificultad para respirar "
    "o un dolor que no cede. No esperes a que pase."
)


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
        query_norm = _normalizar_texto(query)
        mensaje_crisis = None
        if any(f in query_norm for f in FRASES_CRISIS_EMOCIONAL):
            mensaje_crisis = MENSAJE_CRISIS_EMOCIONAL
        elif any(f in query_norm for f in FRASES_URGENCIA_FISICA):
            mensaje_crisis = MENSAJE_URGENCIA_FISICA
        if mensaje_crisis:
            return Response({
                'respuesta': mensaje_crisis,
                'articulo_relacionado': None,
                'opciones_sugeridas': ["Volver al menú principal"],
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

        temas_principales = TEMAS_PRINCIPALES

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
        carrusel_articulos = {
            "¿cómo gestionar la ansiedad o el impacto emocional del diagnóstico?": "más allá del dolor",
            "¿cómo puedo manejar la fatiga crónica asociada a la endometriosis?": "más allá del dolor",
            "¿qué puedo hacer durante un brote (flare-up) de dolor agudo?": "dolor crónico",
        }
        articulo_carrusel = None
        if query_lower in carrusel_articulos:
            art = ContenidoEducativo.objects.filter(
                titulo__icontains=carrusel_articulos[query_lower]
            ).first()
            if art:
                articulo_carrusel = ContenidoEducativoSerializer(art, context={'request': request}).data

        # ---------------------------------------------------------------------
        # (4) CONSULTAS RAG (25 SUBPREGUNTAS O TEXTO LIBRE)
        # ---------------------------------------------------------------------
        try:
            respuesta_rag = generar_respuesta_rag(query)
        except (ImproperlyConfigured, RagError) as e:
            logger.warning("Chatbot sin IA, se usa respaldo de knowledge_base.md: %s", e)
            respuesta_rag = respuesta_local_kb(query)

        return Response({
            'respuesta': respuesta_rag,
            'articulo_relacionado': articulo_carrusel,
            'opciones_sugeridas': ["Volver al menú principal"],
            'preguntas_sugeridas': sugeridas_serializer.data,
        })
