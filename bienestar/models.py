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

    class Meta:
        verbose_name = "Profesional"
        verbose_name_plural = "Profesionales"

    def __str__(self):
        return f"{self.name} - {self.specialty}"


# ==============================================================================
# MÓDULO: COMUNIDAD (Feed, Moderación, Likes, Comentarios, Reportes)
# ==============================================================================
class Publicacion(models.Model):
    ESTADOS = (
        ('PENDIENTE', 'Pendiente'),
        ('APROBADO', 'Aprobado'),
        ('RECHAZADO', 'Rechazado'),
    )

    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='publicaciones', null=True, blank=True, verbose_name="Autora")
    contenido = models.TextField(verbose_name="Contenido del texto")
    imagen = models.ImageField(upload_to='comunidad/', blank=True, null=True, verbose_name="Imagen adjunta")
    estado = models.CharField(max_length=20, choices=ESTADOS, default='APROBADO')
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de publicación")

    class Meta:
        verbose_name = "Publicación"
        verbose_name_plural = "Publicaciones"
        ordering = ['-fecha_creacion']

    def __str__(self):
        nombre = self.usuario.username if self.usuario else "Anónima"
        return f"Publicación de {nombre} - [{self.estado}] - {self.fecha_creacion.strftime('%Y-%m-%d %H:%M')}"


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