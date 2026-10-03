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

class ReglaPuntos(models.Model):
    """Regla configurable desde /admin/: cuántos puntos da cada acción."""
    clave = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=150)
    puntos = models.PositiveIntegerField()
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.clave}: {self.puntos} pts"


class NivelGamificacion(models.Model):
    """Umbrales de nivel, también configurables desde /admin/."""
    nombre = models.CharField(max_length=50)
    puntos_minimos = models.PositiveIntegerField(unique=True)

    class Meta:
        ordering = ['puntos_minimos']

    def __str__(self):
        return f"{self.nombre} (desde {self.puntos_minimos} pts)"


class Gamificacion(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gamificacion',
    )
    puntos_totales = models.PositiveIntegerField(default=0)
    racha_actual = models.PositiveIntegerField(default=0)
    racha_maxima = models.PositiveIntegerField(default=0)
    ultimo_dia_activo = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.usuario.username}: {self.puntos_totales} pts, racha {self.racha_actual}"


class MovimientoPuntos(models.Model):
    """Historial: una fila por cada vez que la usuaria ganó puntos."""
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='movimientos_puntos',
    )
    fecha = models.DateField()
    clave = models.CharField(max_length=50)
    motivo = models.CharField(max_length=150)
    puntos = models.PositiveIntegerField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado_en']

    def __str__(self):
        return f"{self.usuario.username} +{self.puntos} ({self.motivo})"

class RegistroCiclo(models.Model):
    class Abundancia(models.TextChoices):
        LEVE = 'leve', 'Leve'
        MODERADA = 'moderada', 'Moderada'
        ABUNDANTE = 'abundante', 'Abundante'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='registros_ciclo',
    )
    fecha_inicio = models.DateField()
    fecha_fin = models.DateField(null=True, blank=True)
    abundancia = models.CharField(max_length=10, choices=Abundancia.choices)

    class Meta:
        ordering = ['-fecha_inicio']

    def __str__(self):
        return f"{self.usuario.username}: {self.fecha_inicio} ({self.abundancia})"