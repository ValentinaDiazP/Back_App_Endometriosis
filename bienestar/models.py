from django.db import models
from django.contrib.auth.models import User

# ==============================================================================
# MÓDULO: PROFESIONALES
# ==============================================================================
class Professional(models.Model):
    name = models.CharField(max_length=150, verbose_name="Nombre Completo")
    specialty = models.CharField(max_length=150, verbose_name="Especialidad")
    rate = models.CharField(max_length=50, verbose_name="Tarifa")
    availability = models.CharField(max_length=100, verbose_name="Disponibilidad")
    whatsapp = models.CharField(
        max_length=20,
        blank=True,
        default='',
        verbose_name="WhatsApp",
        help_text="Número con código de país, sin espacios (ej: 573001112233)",
    )

    class Meta:
        verbose_name = "Profesional"
        verbose_name_plural = "Profesionales"

    def __str__(self):
        return f"{self.name} - {self.specialty}"


class DisponibilidadProfesional(models.Model):
    profesional = models.ForeignKey(Professional, on_delete=models.CASCADE, related_name='horarios_disponibles', verbose_name="Profesional")
    dia_semana = models.CharField(max_length=20, verbose_name="Día de la semana (ej: Lunes, Martes...)")
    hora_inicio = models.TimeField(verbose_name="Hora de inicio")
    hora_fin = models.TimeField(verbose_name="Hora de fin")

    class Meta:
        verbose_name = "Disponibilidad del Profesional"
        verbose_name_plural = "Disponibilidades de Profesionales"

    def __str__(self):
        return f"{self.profesional.name} - {self.dia_semana} ({self.hora_inicio} a {self.hora_fin})"


class CitaMedica(models.Model):
    ESTADOS_CITA = (
        ('PROGRAMADA', 'Programada (Azul)'),
        ('CONFIRMADA', 'Confirmada (Verde)'),
        ('COMPLETADA', 'Completada (Amarillo)'),
        ('CANCELADA', 'Cancelada (Rojo)'),
    )

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='citas_medicas', verbose_name="Usuaria")
    especialista = models.ForeignKey(Professional, on_delete=models.SET_NULL, null=True, blank=True, related_name='citas', verbose_name="Especialista")
    nombre_especialista = models.CharField(max_length=150, blank=True, default='', verbose_name="Nombre especialista externo")
    especialidad = models.CharField(max_length=150, verbose_name="Especialidad")
    fecha_hora = models.DateTimeField(verbose_name="Fecha y hora de la cita")
    lugar_o_link = models.CharField(max_length=255, blank=True, default='', verbose_name="Lugar o Link de atención")
    estado = models.CharField(max_length=30, choices=ESTADOS_CITA, default='PROGRAMADA', verbose_name="Estado de la cita")
    notas = models.TextField(blank=True, default='', verbose_name="Notas adicionales")
    puntos_otorgados = models.BooleanField(default=False, verbose_name="¿Puntos de gamificación otorgados?")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")

    class Meta:
        verbose_name = "Cita Médica"
        verbose_name_plural = "Citas Médicas"
        ordering = ['fecha_hora']

    def __str__(self):
        esp = self.especialista.name if self.especialista else self.nombre_especialista
        return f"Cita de {self.usuario.username} con {esp} el {self.fecha_hora} [{self.estado}]"


# ==============================================================================
# MÓDULO: COMUNIDAD (Feed, Moderación, Likes, Comentarios, Reportes)
# ==============================================================================
class Publicacion(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
    )

    CATEGORIAS = (
        ('DIAGNOSTICO_TRATAMIENTO', 'Diagnóstico y Tratamiento'),
        ('ESTILO_VIDA', 'Alimentación y Estilo de Vida'),
        ('HISTORIAS_APOYO', 'Historias y Apoyo Emocional'),
    )

    # Se guarda siempre la autora real para trazabilidad en el panel de administración,
    # aunque es_anonimo oculte el nombre en la API pública.
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='publicaciones', null=True, blank=True, verbose_name="Autora")
    contenido = models.TextField(verbose_name="Contenido del texto")
    imagen = models.ImageField(upload_to='comunidad/', blank=True, null=True, verbose_name="Imagen adjunta")
    estado = models.CharField(max_length=30, choices=ESTADOS, default='APROBADO')
    categoria = models.CharField(max_length=50, choices=CATEGORIAS, default='HISTORIAS_APOYO', verbose_name="Categoría de hilo")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de publicación")
    es_anonimo = models.BooleanField(default=False, verbose_name="Publicación anónima")

    class Meta:
        verbose_name = "Publicación"
        verbose_name_plural = "Publicaciones"
        ordering = ['-fecha_creacion']

    def __str__(self):
        return f"Publicación de {self.usuario} - Anónimo: {self.es_anonimo}"

class MeGusta(models.Model):
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name='likes', verbose_name="Publicación")
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='likes', verbose_name="Usuaria")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")

    class Meta:
        verbose_name = "Me gusta"
        verbose_name_plural = "Me gusta"
        unique_together = ('publicacion', 'usuario')

    def __str__(self):
        return f"Like de {self.usuario.username} en post #{self.publicacion.id}"


class Comentario(models.Model):
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name='comentarios', verbose_name="Publicación")
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comentarios', null=True, blank=True, verbose_name="Autora del comentario")
    texto = models.TextField(verbose_name="Texto del comentario")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del comentario")

    class Meta:
        verbose_name = "Comentario"
        verbose_name_plural = "Comentarios"
        ordering = ['fecha_creacion']

    def __str__(self):
        nombre = self.usuario.username if self.usuario else "Anónima"
        return f"Comentario de {nombre} en post #{self.publicacion.id}"


class ReportePublicacion(models.Model):
    publicacion = models.ForeignKey(Publicacion, on_delete=models.CASCADE, related_name='reportes', verbose_name="Publicación reportada")
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reportes_creados', verbose_name="Usuaria que reporta")
    motivo = models.TextField(verbose_name="Motivo del reporte")
    resuelto = models.BooleanField(default=False, verbose_name="Resuelto")
    fecha_reporte = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del reporte")

    class Meta:
        verbose_name = "Reporte de publicación"
        verbose_name_plural = "Reportes de publicaciones"
        ordering = ['-fecha_reporte']

    def __str__(self):
        return f"Reporte sobre post #{self.publicacion.id} por {self.usuario.username}"


class SolicitudContacto(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('ATENDIDA', 'Atendida'),
        ('CANCELADA', 'Cancelada'),
    )

    usuario = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='solicitudes_contacto',
        verbose_name="Usuaria",
    )
    profesional = models.ForeignKey(
        Professional,
        on_delete=models.CASCADE,
        related_name='solicitudes_contacto',
        verbose_name="Profesional",
    )
    fecha_solicitud = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de solicitud")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PENDIENTE', verbose_name="Estado")

    class Meta:
        verbose_name = "Solicitud de contacto"
        verbose_name_plural = "Solicitudes de contacto"
        ordering = ['-fecha_solicitud']

    def __str__(self):
        return f"Solicitud de {self.usuario} a {self.profesional} ({self.estado})"


# ==============================================================================
# MÓDULO: TIENDA VIRTUAL DE BIENESTAR
# ==============================================================================
class Producto(models.Model):
    CATEGORIAS_TIENDA = (
        ('COPAS_MENSTRUALES', 'Copas Menstruales'),
        ('KITS', 'Kits'),
        ('ALIVIO_DOLOR', 'Alivio del Dolor'),
        ('YOGA_EJERCICIO', 'Yoga y Ejercicio'),
        ('LIBROS_DIGITALES', 'Libros Digitales'),
    )

    nombre = models.CharField(max_length=200, verbose_name="Nombre del Producto")
    descripcion = models.TextField(verbose_name="Descripción")
    precio = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")
    marca = models.CharField(max_length=100, default='Vital', verbose_name="Marca Aliada")
    categoria = models.CharField(max_length=50, choices=CATEGORIAS_TIENDA, verbose_name="Categoría")
    imagen_url = models.URLField(max_length=500, verbose_name="URL de Imagen")
    disponible = models.BooleanField(default=True, verbose_name="Disponible")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"

    def __str__(self):
        return f"{self.nombre} - {self.marca} (${self.precio})"


class ItemCarrito(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carrito_items', verbose_name="Usuaria")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, verbose_name="Producto")
    cantidad = models.PositiveIntegerField(default=1, verbose_name="Cantidad")
    agregado_en = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de agregado")

    class Meta:
        verbose_name = "Item de Carrito"
        verbose_name_plural = "Items de Carrito"

    def __str__(self):
        return f"{self.cantidad}x {self.producto.nombre} ({self.usuario.username})"


class OrdenCompra(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ordenes_compra', verbose_name="Usuaria")
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total Pagado")
    completada = models.BooleanField(default=True, verbose_name="Completada")
    fecha_compra = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Compra")
    items_snapshot = models.TextField(blank=True, default='', verbose_name="Resumen de Productos")

    class Meta:
        verbose_name = "Orden de Compra"
        verbose_name_plural = "Órdenes de Compra"
        ordering = ['-fecha_compra']

    def __str__(self):
        return f"Orden #{self.id} - {self.usuario.username} (${self.total})"
