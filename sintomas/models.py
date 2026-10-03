from django.conf import settings
from django.db import models


class LocalizacionDolor(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class SintomaAsociado(models.Model):
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre


class RegistroSintoma(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='registros_sintoma',
    )
    fecha_hora = models.DateTimeField(auto_now_add=True)
    intensidad_dolor = models.PositiveSmallIntegerField()
    localizaciones = models.ManyToManyField(LocalizacionDolor, blank=True, related_name='registros')
    localizacion_otro_detalle = models.CharField(max_length=150, null=True, blank=True)
    sintomas_asociados = models.ManyToManyField(SintomaAsociado, blank=True, related_name='registros')
    observacion = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-fecha_hora']

    def __str__(self):
        return f"Registro de {self.usuario.username} - {self.fecha_hora}"


class RegistroEmocional(models.Model):
    """
    Check-in emocional diario: un solo registro por usuaria y día (no por
    hora), que se actualiza si ya existe en vez de duplicarse — la racha
    de Gamificación necesita una pregunta binaria por día ("¿registró hoy?"),
    no múltiples entradas sueltas.
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='registros_emocionales',
    )
    fecha = models.DateField(auto_now_add=True)
    estado_animo = models.PositiveSmallIntegerField()  # Escala 1-5 (emojis)
    nota_libre = models.TextField(null=True, blank=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['usuario', 'fecha']
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.usuario.username} - {self.fecha} - ánimo {self.estado_animo}"