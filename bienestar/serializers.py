from rest_framework import serializers
from .models import Professional, DisponibilidadProfesional, CitaMedica, Publicacion, Comentario, SolicitudContacto
from sintomas.gamificacion import registrar_actividad


class DisponibilidadProfesionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisponibilidadProfesional
        fields = ['id', 'dia_semana', 'hora_inicio', 'hora_fin']


class ProfessionalSerializer(serializers.ModelSerializer):
    horarios_disponibles = DisponibilidadProfesionalSerializer(many=True, read_only=True)

    class Meta:
        model = Professional
        fields = ['id', 'name', 'specialty', 'rate', 'availability', 'whatsapp', 'horarios_disponibles']


class CitaMedicaSerializer(serializers.ModelSerializer):
    especialista_nombre = serializers.SerializerMethodField()

    class Meta:
        model = CitaMedica
        fields = [
            'id', 'usuario', 'especialista', 'especialista_nombre', 'nombre_especialista',
            'especialidad', 'fecha_hora', 'lugar_o_link', 'estado', 'notas',
            'puntos_otorgados', 'fecha_creacion'
        ]
        read_only_fields = ['usuario', 'puntos_otorgados', 'fecha_creacion']

    def get_especialista_nombre(self, obj):
        if obj.especialista:
            return obj.especialista.name
        return obj.nombre_especialista

    def update(self, instance, validated_data):
        nuevo_estado = validated_data.get('estado', instance.estado)
        if nuevo_estado == 'COMPLETADA' and not instance.puntos_otorgados:
            registrar_actividad(instance.usuario, 'cita_completada')
            validated_data['puntos_otorgados'] = True
        return super().update(instance, validated_data)


class ComentarioSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Comentario
        fields = ['id', 'publicacion', 'usuario', 'usuario_nombre', 'texto', 'fecha_creacion']
        read_only_fields = ['usuario', 'fecha_creacion']

    def get_usuario_nombre(self, obj):
        if obj.usuario:
            return obj.usuario.get_full_name() or obj.usuario.username or "Anónima"
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
            'id', 'contenido', 'imagen', 'fecha_creacion',
            'estado', 'es_anonimo', 'categoria', 'usuario_nombre',
            'total_likes', 'me_gusta', 'total_comentarios', 'comentarios',
        ]
        read_only_fields = ['estado']

    def get_usuario_nombre(self, obj):
        if obj.es_anonimo:
            return "Anónima"
        if obj.usuario:
            return obj.usuario.get_full_name() or obj.usuario.username
        return "Anónima"

    def get_total_likes(self, obj):
        return obj.likes.count()

    def get_me_gusta(self, obj):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            return obj.likes.filter(usuario=request.user).exists()
        return False

    def get_total_comentarios(self, obj):
        return obj.comentarios.count()


class SolicitudContactoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SolicitudContacto
        fields = ['id', 'usuario', 'profesional', 'fecha_solicitud', 'estado']
        read_only_fields = ['usuario', 'fecha_solicitud']
