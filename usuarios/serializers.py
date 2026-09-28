from django.contrib.auth.models import User
from rest_framework import serializers

from .models import PerfilUsuaria


class RegistroSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=6)
    nombre = serializers.CharField(max_length=150)
    fecha_nacimiento = serializers.DateField()
    diagnostico = serializers.CharField(max_length=100, required=False, allow_blank=True)
    fecha_diagnostico = serializers.DateField(required=False, allow_null=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('Ese nombre de usuario ya existe, elige otro.')
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data['nombre'],
        )
        PerfilUsuaria.objects.create(
            usuario=user,
            fecha_nacimiento=validated_data['fecha_nacimiento'],
            fecha_diagnostico=validated_data.get('fecha_diagnostico'),
            diagnostico=validated_data.get('diagnostico') or None,
        )
        return user


class PerfilSerializer(serializers.ModelSerializer):
    """Usado por /me/ para devolver el perfil completo tras el login."""
    usuario_id = serializers.IntegerField(source='usuario.id', read_only=True)
    username = serializers.CharField(source='usuario.username', read_only=True)
    nombre = serializers.CharField(source='usuario.first_name', read_only=True)
    edad = serializers.ReadOnlyField()

    class Meta:
        model = PerfilUsuaria
        fields = [
            'usuario_id', 'username', 'nombre', 'fecha_nacimiento', 'fecha_diagnostico',
            'diagnostico', 'edad', 'onboarding_completado',
        ]