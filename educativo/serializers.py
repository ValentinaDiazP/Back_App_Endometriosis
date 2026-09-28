from rest_framework import serializers

from .models import (
    CategoriaContenido,
    ContenidoEducativo,
    EjercicioPsicoeducativo,
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
