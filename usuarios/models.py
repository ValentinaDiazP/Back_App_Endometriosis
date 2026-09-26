from datetime import date

from django.conf import settings
from django.db import models


class PerfilUsuaria(models.Model):
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='perfil',
    )
    fecha_nacimiento = models.DateField()
    fecha_diagnostico = models.DateField(null=True, blank=True)
    diagnostico = models.CharField(max_length=100, null=True, blank=True)

    # True una vez que la usuaria completó, alguna vez, el flujo de
    # diagnóstico + cuestionario inicial. Controla si el próximo login
    # la manda directo al menú principal o repite ese flujo una vez más.
    onboarding_completado = models.BooleanField(default=False)

    @property
    def edad(self):
        """Calculada a partir de fecha_nacimiento, nunca almacenada
        (así nunca queda desactualizada)."""
        hoy = date.today()
        años = hoy.year - self.fecha_nacimiento.year
        if (hoy.month, hoy.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day):
            años -= 1
        return años

    def __str__(self):
        return f"Perfil de {self.usuario.username}"