from rest_framework import serializers
from .models import (
    Professional, DisponibilidadProfesional, CitaMedica, 
    Publicacion, Comentario, MeGustaComentario, SolicitudContacto, 
    Producto, ItemCarrito, OrdenCompra
)
from sintomas.gamificacion import registrar_actividad


class DisponibilidadProfesionalSerializer(serializers.ModelSerializer):
    class Meta:
        model = DisponibilidadProfesional
        fields = ['id', 'dia_semana', 'hora_inicio', 'hora_fin']


class ProfessionalSerializer(serializers.ModelSerializer):
    horarios_disponibles = DisponibilidadProfesionalSerializer(many=True, read_only=True)

    class Meta:
        model = Professional
        fields = ['id', 'name', 'specialty', 'rate', 'availability', 'whatsapp', 'google_calendar_id', 'atiende_virtual', 'atiende_presencial', 'horarios_disponibles']


class CitaMedicaSerializer(serializers.ModelSerializer):
    especialista_nombre = serializers.SerializerMethodField()

    class Meta:
        model = CitaMedica
        fields = [
            'id', 'usuario', 'especialista', 'especialista_nombre', 'nombre_especialista',
            'especialidad', 'modalidad', 'fecha_hora', 'lugar_o_link', 'estado', 'notas',
            'puntos_otorgados', 'fecha_creacion'
        ]
        read_only_fields = ['usuario', 'puntos_otorgados', 'fecha_creacion']

    def get_especialista_nombre(self, obj):
        if obj.especialista:
            return obj.especialista.name
        return obj.nombre_especialista

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user and request.user.is_authenticated:
            validated_data['usuario'] = request.user
        
        cita = super().create(validated_data)
        
        # Gamificación de continuidad (3 citas con el mismo profesional)
        if cita.usuario and cita.especialista:
            registrar_actividad(cita.usuario, 'cita_medica')
            citas_count = CitaMedica.objects.filter(usuario=cita.usuario, especialista=cita.especialista).count()
            if citas_count >= 3:
                registrar_actividad(cita.usuario, 'vinculo_confianza')
        elif cita.usuario:
            registrar_actividad(cita.usuario, 'cita_medica')

        return cita

    def update(self, instance, validated_data):
        nuevo_estado = validated_data.get('estado', instance.estado)
        if nuevo_estado == 'COMPLETADA' and not instance.puntos_otorgados:
            registrar_actividad(instance.usuario, 'cita_completada')
            validated_data['puntos_otorgados'] = True
        return super().update(instance, validated_data)


class ComentarioSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.SerializerMethodField()
    total_likes = serializers.SerializerMethodField()

    class Meta:
        model = Comentario
        fields = ['id', 'publicacion', 'usuario', 'usuario_nombre', 'texto', 'fecha_creacion', 'total_likes']
        read_only_fields = ['usuario', 'fecha_creacion']

    def get_usuario_nombre(self, obj):
        if obj.usuario:
            return obj.usuario.get_full_name() or obj.usuario.username or "Anónima"
        return "Anónima"

    def get_total_likes(self, obj):
        return obj.likes.count()


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


class ProductoRelacionadoSerializer(serializers.ModelSerializer):
    imagen_final = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'descripcion', 'composicion', 'precio', 'marca',
            'categoria', 'imagen_url', 'imagen', 'imagen_final', 'rating',
            'reviews_count', 'disponible'
        ]

    def get_imagen_final(self, obj):
        if obj.imagen:
            request = self.context.get('request')
            url = request.build_absolute_uri(obj.imagen.url) if request else obj.imagen.url
            return url.replace('http://127.0.0.1:8000', 'http://10.0.2.2:8000').replace('http://localhost:8000', 'http://10.0.2.2:8000')
        if obj.imagen_url:
            return obj.imagen_url.replace('http://127.0.0.1:8000', 'http://10.0.2.2:8000').replace('http://localhost:8000', 'http://10.0.2.2:8000')
        return ''


class ProductoSerializer(serializers.ModelSerializer):
    imagen_final = serializers.SerializerMethodField()
    productos_relacionados = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            'id', 'nombre', 'descripcion', 'composicion', 'precio', 'marca',
            'categoria', 'imagen_url', 'imagen', 'imagen_final', 'rating',
            'reviews_count', 'disponible', 'productos_relacionados'
        ]

    def get_imagen_final(self, obj):
        if obj.imagen:
            request = self.context.get('request')
            url = request.build_absolute_uri(obj.imagen.url) if request else obj.imagen.url
            return url.replace('http://127.0.0.1:8000', 'http://10.0.2.2:8000').replace('http://localhost:8000', 'http://10.0.2.2:8000')
        if obj.imagen_url:
            return obj.imagen_url.replace('http://127.0.0.1:8000', 'http://10.0.2.2:8000').replace('http://localhost:8000', 'http://10.0.2.2:8000')
        return ''

    def get_productos_relacionados(self, obj):
        relacionados = Producto.objects.filter(categoria=obj.categoria, disponible=True).exclude(id=obj.id)[:4]
        return ProductoRelacionadoSerializer(relacionados, many=True, context=self.context).data


class ItemCarritoSerializer(serializers.ModelSerializer):
    producto_detalle = ProductoSerializer(source='producto', read_only=True)

    class Meta:
        model = ItemCarrito
        fields = ['id', 'usuario', 'producto', 'producto_detalle', 'cantidad', 'agregado_en']
        read_only_fields = ['usuario', 'agregado_en']


class OrdenCompraSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdenCompra
        fields = ['id', 'usuario', 'total', 'completada', 'fecha_compra', 'items_snapshot']
        read_only_fields = ['usuario', 'total', 'completada', 'fecha_compra', 'items_snapshot']

