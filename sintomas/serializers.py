from rest_framework import serializers

from .models import LocalizacionDolor, RegistroCiclo, RegistroEmocional, RegistroSintoma, SintomaAsociado

class LocalizacionDolorSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalizacionDolor
        fields = ['id', 'nombre']


class SintomaAsociadoSerializer(serializers.ModelSerializer):
    class Meta:
        model = SintomaAsociado
        fields = ['id', 'nombre']


class RegistroSintomaSerializer(serializers.ModelSerializer):
    # Para escribir: solo se envían los IDs de catálogo seleccionados.
    localizaciones = serializers.PrimaryKeyRelatedField(
        many=True, queryset=LocalizacionDolor.objects.all(), required=False
    )
    sintomas_asociados = serializers.PrimaryKeyRelatedField(
        many=True, queryset=SintomaAsociado.objects.all(), required=False
    )
    # Para leer: se devuelve también el nombre, no solo el ID.
    localizaciones_detalle = LocalizacionDolorSerializer(source='localizaciones', many=True, read_only=True)
    sintomas_asociados_detalle = SintomaAsociadoSerializer(source='sintomas_asociados', many=True, read_only=True)

    class Meta:
        model = RegistroSintoma
        fields = [
            'id', 'fecha_hora', 'intensidad_dolor',
            'localizaciones', 'localizaciones_detalle', 'localizacion_otro_detalle',
            'sintomas_asociados', 'sintomas_asociados_detalle', 'observacion',
        ]
        read_only_fields = ['id', 'fecha_hora']

class RegistroEmocionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroEmocional
        fields = ['id', 'fecha', 'estado_animo', 'nota_libre', 'actualizado_en']
        read_only_fields = ['id', 'fecha', 'actualizado_en']

class RegistroCicloSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroCiclo
        fields = ['id', 'fecha_inicio', 'fecha_fin', 'abundancia']
        read_only_fields = ['id']

    def validate(self, datos):
        inicio = datos.get('fecha_inicio', getattr(self.instance, 'fecha_inicio', None))
        fin = datos.get('fecha_fin', getattr(self.instance, 'fecha_fin', None))
        if inicio and fin and fin < inicio:
            raise serializers.ValidationError(
                'La fecha de fin no puede ser anterior a la de inicio.'
            )
        return datos