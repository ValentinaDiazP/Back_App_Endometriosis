from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth.models import User

from . import google_calendar
import datetime
import threading
from .models import (
    Publicacion, Comentario, Professional, DisponibilidadProfesional, 
    CitaMedica, MeGusta, ReportePublicacion, SolicitudContacto,
    Producto, ItemCarrito, OrdenCompra
)
from .serializers import (
    PublicacionSerializer,
    ComentarioSerializer,
    ProfessionalSerializer,
    DisponibilidadProfesionalSerializer,
    CitaMedicaSerializer,
    SolicitudContactoSerializer,
    ProductoSerializer,
    ItemCarritoSerializer,
    OrdenCompraSerializer,
)


class ProfessionalViewSet(viewsets.ModelViewSet):
    queryset = Professional.objects.all()
    serializer_class = ProfessionalSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=['get'])
    def disponibilidad(self, request, pk=None):
        profesional = self.get_object()
        fecha = request.query_params.get('fecha')
        if not fecha:
            fecha = datetime.date.today().strftime('%Y-%m-%d')
        
        horarios = google_calendar.obtener_horarios_disponibles(profesional.google_calendar_id, fecha)
        return Response(horarios)


class CitaMedicaViewSet(viewsets.ModelViewSet):
    serializer_class = CitaMedicaSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CitaMedica.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        cita = serializer.save(usuario=self.request.user, estado='PROGRAMADA')
        
        # Sincronizar con Google Calendar en segundo plano
        if cita.especialista and cita.especialista.google_calendar_id:
            calendar_id = cita.especialista.google_calendar_id
            resumen = f"Cita Médica: {cita.usuario.username} - {cita.especialidad}"
            inicio = cita.fecha_hora
            fin = inicio + datetime.timedelta(hours=1)
            descripcion = f"Cita agendada vía app Bienestar. Notas: {cita.notas}"
            
            def tarea_segundo_plano():
                google_calendar.crear_evento_cita(calendar_id, resumen, inicio, fin, descripcion)
                
            threading.Thread(target=tarea_segundo_plano).start()

    @action(detail=True, methods=['get'], url_path='reporte-salud')
    def reporte_salud(self, request, pk=None):
        cita = self.get_object()
        reporte_data = {
            "cita_id": cita.id,
            "paciente": cita.usuario.username,
            "especialidad": cita.especialidad,
            "especialista": cita.especialista.name if cita.especialista else cita.nombre_especialista,
            "fecha_hora": cita.fecha_hora,
            "estado": cita.estado,
            "notas": cita.notas,
            "resumen_salud": {
                "sintomas_recientes": [],
                "ultimos_registros_emocionales": [],
                "recomendaciones_previas": []
            }
        }
        return Response(reporte_data, status=status.HTTP_200_OK)


class PublicacionViewSet(viewsets.ModelViewSet):
    serializer_class = PublicacionSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = Publicacion.objects.filter(estado='APROBADO').order_by('-fecha_creacion')
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(usuario=user, estado='APROBADO')
        if user is not None:
            registrar_actividad(user, 'comunidad_post')

    @action(detail=True, methods=['post'])
    def reaccionar(self, request, pk=None):
        publicacion = self.get_object()
        usuario = request.user

        if not usuario.is_authenticated:
            return Response(
                {'error': 'Debes iniciar sesión para dar me gusta'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        megusta, created = MeGusta.objects.get_or_create(publicacion=publicacion, usuario=usuario)

        if not created:
            megusta.delete()
            return Response({'status': 'Like eliminado', 'me_gusta': False}, status=status.HTTP_200_OK)

        return Response({'status': 'Like agregado', 'me_gusta': True}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], permission_classes=[permissions.AllowAny])
    def comentar(self, request, pk=None):
        publicacion = self.get_object()
        user = request.user if request.user.is_authenticated else None
        texto = request.data.get('texto', '').strip()

        if not texto:
            return Response(
                {'error': 'El comentario no puede estar vacío.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        comentario = Comentario.objects.create(publicacion=publicacion, usuario=user, texto=texto)
        if user is not None:
            registrar_actividad(user, 'comunidad_comentario')
        serializer = ComentarioSerializer(comentario)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def reportar(self, request, pk=None):
        publicacion = self.get_object()
        motivo = request.data.get('motivo', '')

        if not request.user.is_authenticated:
            return Response(
                {'error': 'Debes iniciar sesión para reportar una publicación'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        ReportePublicacion.objects.create(
            publicacion=publicacion,
            usuario=request.user,
            motivo=motivo,
        )

        publicacion.estado = 'PENDIENTE'
        publicacion.save()

        return Response(
            {'status': 'Publicación reportada y enviada a revisión'},
            status=status.HTTP_200_OK,
        )


class ComentarioViewSet(viewsets.ModelViewSet):
    queryset = Comentario.objects.all()
    serializer_class = ComentarioSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        user = self.request.user if self.request.user.is_authenticated else None
        serializer.save(usuario=user)
        if user is not None:
            registrar_actividad(user, 'comunidad_comentario')


class SolicitudContactoViewSet(viewsets.ModelViewSet):
    serializer_class = SolicitudContactoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SolicitudContacto.objects.filter(usuario=self.request.user)

    def perform_create(self, serializer):
        serializer.save(usuario=self.request.user, estado='PENDIENTE')


class ProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.filter(disponible=True)
    serializer_class = ProductoSerializer
    permission_classes = [permissions.AllowAny]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        relacionados = Producto.objects.filter(categoria=instance.categoria, disponible=True).exclude(id=instance.id)[:4]
        relacionados_serializer = self.get_serializer(relacionados, many=True)
        data = serializer.data
        data['productos_relacionados'] = relacionados_serializer.data
        return Response(data)


class CarritoViewSet(viewsets.ModelViewSet):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = ItemCarritoSerializer

    def get_usuario(self, request):
        if request.user and request.user.is_authenticated:
            return request.user
        user = User.objects.first()
        if not user:
            user = User.objects.create_user(username='test_user', email='test@example.com')
        return user

    def get_queryset(self):
        usuario = self.get_usuario(self.request)
        return ItemCarrito.objects.filter(usuario=usuario)

    def create(self, request, *args, **kwargs):
        usuario = self.get_usuario(request)
        producto_id = request.data.get('producto_id') or request.data.get('producto')
        cantidad = int(request.data.get('cantidad', 1))

        if not producto_id:
            return Response({'error': 'producto_id es requerido'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            return Response({'error': 'Producto no encontrado'}, status=status.HTTP_404_NOT_FOUND)

        item, created = ItemCarrito.objects.get_or_create(
            usuario=usuario,
            producto=producto,
            defaults={'cantidad': cantidad}
        )

        if not created:
            item.cantidad += cantidad
            item.save()

        serializer = self.get_serializer(item)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ComprarViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='confirmar')
    def confirmar(self, request):
        user = request.user
        items = ItemCarrito.objects.filter(usuario=user)
        if not items.exists():
            return Response({'error': 'El carrito está vacío.'}, status=status.HTTP_400_BAD_REQUEST)

        total = sum(item.producto.precio * item.cantidad for item in items)
        snapshot = ", ".join([f"{item.cantidad}x {item.producto.nombre}" for item in items])

        compras_previas_count = OrdenCompra.objects.filter(usuario=user, completada=True).count()
        es_primera_compra = (compras_previas_count == 0)

        orden = OrdenCompra.objects.create(
            usuario=user,
            total=total,
            completada=True,
            items_snapshot=snapshot
        )

        items.delete()

        gamificacion_otorgada = False
        if es_primera_compra:
            registrar_actividad(user, 'primera_compra_tienda')
            try:
                from sintomas.models import Gamificacion
                gam, _ = Gamificacion.objects.get_or_create(usuario=user)
                gam.puntos += 50
                gam.insignias = (gam.insignia or '') + "Embajadora del Bienestar 🌸; "
                gam.save()
            except Exception:
                pass
            gamificacion_otorgada = True

        return Response({
            'status': 'Compra confirmada con éxito',
            'orden_id': orden.id,
            'total': total,
            'primera_compra': es_primera_compra,
            'gamificacion_otorgada': gamificacion_otorgada,
            'mensaje': '¡Felicidades! Primera compra realizada con éxito.' if es_primera_compra else 'Compra exitosa.'
        }, status=status.HTTP_201_CREATED)