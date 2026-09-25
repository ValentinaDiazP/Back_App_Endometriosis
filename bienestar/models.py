from django.db import models
from django.contrib.auth.models import User

# ==============================================================================
# MÓDULO: PROFESIONALES
# Descripción: Modelos para la gestión de profesionales y directorio de atención.
# ==============================================================================

class Professional(models.Model):
    """
    Representa a un especialista/profesional disponible en la plataforma.
    """
    name = models.CharField(max_length=150, verbose_name="Nombre Completo")
    specialty = models.CharField(max_length=150, verbose_name="Especialidad")
    rate = models.CharField(max_length=50, verbose_name="Tarifa")  # Ej: "$150.000 COP"
    availability = models.CharField(max_length=100, verbose_name="Disponibilidad")  # Ej: "Disponible hoy"

    class Meta:
        verbose_name = "Profesional"
        verbose_name_plural = "Profesionales"

    def __str__(self):
        return f"{self.name} - {self.specialty}"


# ==============================================================================
# MÓDULO: COMUNIDAD (Feed, Publicaciones y Comentarios)
# Descripción: Permite a las usuarias crear publicaciones con texto/imagen y comentar.
# ==============================================================================
class Publicacion(models.Model):
    # TODO: [PENDIENTE REGISTRO] 'null=True' y 'blank=True' son temporales.
    # Cuando se implemente el login/registro, quitar 'null=True, blank=True'
    # para requerir obligatoriamente una usuaria registrada.
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='publicaciones', null=True, blank=True, verbose_name="Autora")
    contenido = models.TextField(verbose_name="Contenido del texto")
    imagen = models.ImageField(upload_to='comunidad/', blank=True, null=True, verbose_name="Imagen adjunta")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de publicación")

    class Meta:
        verbose_name = "Publicación"
        verbose_name_plural = "Publicaciones"
        ordering = ['-fecha_creacion']

    def __str__(self):
        nombre = self.usuario.username if self.usuario else "Anónima"
        return f"Publicación de {nombre} - {self.fecha_creacion.strftime('%Y-%m-%d %H:%M')}"


class Comentario(models.Model):
    # TODO: [PENDIENTE REGISTRO] 'null=True' y 'blank=True' son temporales.
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