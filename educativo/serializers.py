from rest_framework import serializers

from .acceso import esta_bloqueado, premium_de_la_peticion
from .models import (
    CategoriaContenido,
    ContenidoEducativo,
    EjercicioPsicoeducativo,
    InteraccionContenido,
    PreguntaFrecuente,
    RegistroEjercicio,
    RutaAprendizaje,
)


class CategoriaContenidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaContenido
        fields = ['id', 'nombre', 'descripcion']


class _SegmentacionPremiumMixin:
    """
    Agrega `bloqueado` y, si el recurso es premium y la usuaria no, vacía los
    campos con el contenido de verdad (`CAMPOS_PROTEGIDOS`). El título y el
    resumen siguen visibles para que sepa que el recurso existe.

    Sin `request` en el contexto se asume usuaria gratuita (lo seguro).
    """
    CAMPOS_PROTEGIDOS = ()

    def to_representation(self, instance):
        datos = super().to_representation(instance)
        bloqueado = esta_bloqueado(instance, premium_de_la_peticion(self.context.get('request')))
        datos['bloqueado'] = bloqueado
        if bloqueado:
            for campo in self.CAMPOS_PROTEGIDOS:
                datos[campo] = ''
        return datos


class ContenidoEducativoSerializer(_SegmentacionPremiumMixin, serializers.ModelSerializer):
    # Se devuelve solo el id de la categoría (el `idCategoriaFK` del frontend).
    CAMPOS_PROTEGIDOS = ('cuerpo', 'url_recurso')

    class Meta:
        model = ContenidoEducativo
        fields = [
            'id', 'categoria', 'titulo', 'tipo', 'nivel', 'es_premium',
            'fecha_publicacion', 'resumen', 'cuerpo', 'minutos_estimados', 'url_recurso',
        ]


class EjercicioPsicoeducativoSerializer(_SegmentacionPremiumMixin, serializers.ModelSerializer):
    CAMPOS_PROTEGIDOS = ('instrucciones', 'url_recurso')

    class Meta:
        model = EjercicioPsicoeducativo
        fields = [
            'id', 'nombre', 'tipo', 'descripcion', 'instrucciones', 'minutos_estimados',
            'url_recurso', 'es_premium',
        ]


class RutaAprendizajeSerializer(serializers.ModelSerializer):
    # Contenidos completos y en el orden de la ruta, igual que la lista
    # `contenidos` de RutaAprendizaje en Flutter.
    contenidos = serializers.SerializerMethodField()

    class Meta:
        model = RutaAprendizaje
        fields = ['id', 'nombre', 'descripcion', 'contenidos']

    def get_contenidos(self, ruta):
        pasos = ruta.pasos.all()  # ya viene ordenado por `orden`
        return ContenidoEducativoSerializer(
            [p.contenido for p in pasos], many=True, context=self.context
        ).data


class PreferenciasSerializer(serializers.Serializer):
    """Lista completa de categorías preferidas: {"categorias": ["cat_dolor", ...]}"""
    categorias = serializers.ListField(child=serializers.CharField(), allow_empty=True)

    def validate_categorias(self, ids):
        ids = list(dict.fromkeys(ids))  # sin repetidos, conservando el orden
        existentes = set(CategoriaContenido.objects.filter(id__in=ids).values_list('id', flat=True))
        desconocidas = [i for i in ids if i not in existentes]
        if desconocidas:
            raise serializers.ValidationError(f"Categorías inexistentes: {', '.join(desconocidas)}")
        return ids


class InteraccionContenidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = InteraccionContenido
        fields = ['id', 'contenido', 'completado', 'fecha']
        read_only_fields = ['id', 'fecha']
        # La unicidad (usuaria, contenido) la resuelve la vista con
        # update_or_create, así que marcar dos veces no es un error.
        validators = []


class RegistroEjercicioSerializer(serializers.ModelSerializer):
    utilidad = serializers.IntegerField(min_value=1, max_value=5, required=False, allow_null=True)

    class Meta:
        model = RegistroEjercicio
        fields = ['id', 'ejercicio', 'fecha', 'respuestas', 'utilidad']
        read_only_fields = ['id', 'fecha']


class PreguntaFrecuenteSerializer(serializers.ModelSerializer):
    articulo_relacionado = ContenidoEducativoSerializer(read_only=True)

    class Meta:
        model = PreguntaFrecuente
        fields = ['id', 'pregunta', 'respuesta', 'categoria', 'articulo_relacionado']
