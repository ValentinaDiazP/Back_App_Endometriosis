from django.db import models

# Create your models here.
from django.db import models

class Professional(models.Model):
    name = models.CharField(max_length=150, verbose_name="Nombre Completo")
    specialty = models.CharField(max_length=150, verbose_name="Especialidad")
    rate = models.CharField(max_length=50, verbose_name="Tarifa") # Ej: "$150.000 COP"
    availability = models.CharField(max_length=100, verbose_name="Disponibilidad") # Ej: "Disponible hoy"

    def __str__(self):
        return f"{self.name} - {self.specialty}"