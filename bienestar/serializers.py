from rest_framework import serializers
from .models import Professional, Publicacion, Comentario, MeGusta, ReportePublicacion

class ProfessionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Professional
        fields = '__all__'

class ComentarioSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Comentario
        fields = ['id', 'publicacion', 'usuario', 'usuario_nombre', 'texto', 'fecha_creacion']
        read_only_fields = ['usuario', 'fecha_creacion']

    def get_usuario_nombre(self, obj):
        if obj.usuario:
            return obj.usuario.username or "Anónima"
        return "Anónima"

class PublicacionSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()
    total_likes = serializers.SerializerMethodField()
    me_gusta = serializers.SerializerMethodField()
    total_comentarios = serializers.SerializerMethodField()
    comentarios = ComentarioSerializer(many=True, read_only=True)

    class Meta:
        model = Publicacion
        fields = [
            'id', 'usuario', 'usuario_nombre', 'contenido', 'imagen', 'fecha_creacion',
            'estado', 'total_likes', 'me_gusta', 'total_comentarios', 'comentarios'
        ]
        read_only_fields = ['usuario', 'fecha_creacion']

    def get_usuario_nombre(self, obj):
        if obj.usuario:
            return obj.usuario.username or "Anónima"
        return "Anónima"

    def get_total_likes(self, obj):
        if hasattr(obj, 'megusta_set'):
            return obj.megusta_set.count()
        return 0

    def get_me_gusta(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            if hasattr(obj, 'megusta_set'):
                return obj.megusta_set.filter(usuario=request.user).exists()
        return False

    def get_total_comentarios(self, obj):
        if hasattr(obj, 'comentarios'):
            return obj.comentarios.count()
        return obj.comentario_set.count()