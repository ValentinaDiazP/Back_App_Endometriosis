from rest_framework import serializers
from .models import Professional
from rest_framework import serializers
from .models import Publicacion, Comentario

class ProfessionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Professional
        fields = '__all__'

class ComentarioSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.ReadOnlyField(source='usuario.username')

    class Meta:
        model = Comentario
        fields = ['id', 'publicacion', 'usuario', 'usuario_nombre', 'texto', 'fecha_creacion']
        read_only_fields = ['usuario', 'fecha_creacion']


class PublicacionSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.ReadOnlyField(source='usuario.username')
    comentarios = ComentarioSerializer(many=True, read_only=True)
    comentarios_count = serializers.SerializerMethodField()

    class Meta:
        model = Publicacion
        fields = ['id', 'usuario', 'usuario_nombre', 'contenido', 'imagen', 'fecha_creacion', 'comentarios', 'comentarios_count']
        read_only_fields = ['usuario', 'fecha_creacion']

    def get_comentarios_count(self, obj):
        return obj.comentarios.count()