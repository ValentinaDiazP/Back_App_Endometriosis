from rest_framework import serializers

from .models import (
    CategoriaContenido,
    ContenidoEducativo,
    EjercicioPsicoeducativo,
    InteraccionContenido,
    RegistroEjercicio,
    RutaAprendizaje,
)


class CategoriaContenidoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoriaContenido
        fields = ['id', 'nombre', 'descripcion']


class ContenidoEducativoSerializer(serializers.ModelSerializer):
    # Se devuelve solo el id de la categoría (el `idCategoriaFK` del frontend).
    class Meta:
        model = ContenidoEducativo
        fields = [
            'id', 'categoria', 'titulo', 'tipo', 'nivel', 'es_premium',
            'fecha_publicacion', 'resumen', 'cuerpo', 'minutos_estimados',
        ]


class EjercicioPsicoeducativoSerializer(serializers.ModelSerializer):
    class Meta:
        model = EjercicioPsicoeducativo
        fields = ['id', 'nombre', 'tipo', 'descripcion', 'instrucciones', 'minutos_estimados']


class RutaAprendizajeSerializer(serializers.ModelSerializer):
    # Contenidos completos y en el orden de la ruta, igual que la lista
    # `contenidos` de RutaAprendizaje en Flutter.
    contenidos = serializers.SerializerMethodField()

    class Meta:
        model = RutaAprendizaje
        fields = ['id', 'nombre', 'descripcion', 'contenidos']

    def get_contenidos(self, ruta):
        pasos = ruta.pasos.all()  # ya viene ordenado por `orden`
        return ContenidoEducativoSerializer([p.contenido for p in pasos], many=True).data


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
