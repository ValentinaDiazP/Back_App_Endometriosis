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