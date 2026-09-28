from django.db import models


# Los catálogos usan un código de texto como clave primaria (p. ej.
# 'cat_dolor', 'c1', 'e1', 'r1') porque el frontend ya identifica cada
# elemento con esos strings: las preferencias guardan ids de categoría y el
# progreso guarda ids de contenido/ejercicio.
#
# Los valores de los choices coinciden con los nombres de los enums de
# Flutter (TipoContenido, NivelContenido, TipoEjercicio) para poder
# convertirlos directamente con `Enum.values.byName(...)`.


class CategoriaContenido(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'categoría de contenido'
        verbose_name_plural = 'categorías de contenido'

    def __str__(self):
        return self.nombre


class ContenidoEducativo(models.Model):
    class Tipo(models.TextChoices):
        TEXTO = 'texto', 'Texto'
        VIDEO = 'video', 'Video'
        AUDIO = 'audio', 'Audio'

    class Nivel(models.TextChoices):
        BASICO = 'basico', 'Básico'
        INTERMEDIO = 'intermedio', 'Intermedio'
        AVANZADO = 'avanzado', 'Avanzado'

    id = models.CharField(max_length=50, primary_key=True)
    categoria = models.ForeignKey(
        CategoriaContenido,
        on_delete=models.PROTECT,
        related_name='contenidos',
    )
    titulo = models.CharField(max_length=200)
    tipo = models.CharField(max_length=10, choices=Tipo.choices)
    nivel = models.CharField(max_length=12, choices=Nivel.choices)
    es_premium = models.BooleanField(default=False)
    fecha_publicacion = models.DateField()
    resumen = models.CharField(max_length=300)
    cuerpo = models.TextField()
    minutos_estimados = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['fecha_publicacion', 'id']
        verbose_name = 'contenido educativo'
        verbose_name_plural = 'contenidos educativos'

    def __str__(self):
        return self.titulo


class EjercicioPsicoeducativo(models.Model):
    class Tipo(models.TextChoices):
        PSICOEDUCACION = 'psicoeducacion', 'Psicoeducación'
        TCC = 'tcc', 'TCC'
        ACT_MINDFULNESS = 'actMindfulness', 'ACT y Mindfulness'

    id = models.CharField(max_length=50, primary_key=True)
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    descripcion = models.TextField()
    instrucciones = models.TextField()
    minutos_estimados = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['id']
        verbose_name = 'ejercicio psicoeducativo'
        verbose_name_plural = 'ejercicios psicoeducativos'

    def __str__(self):
        return self.nombre


class RutaAprendizaje(models.Model):
    id = models.CharField(max_length=50, primary_key=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    contenidos = models.ManyToManyField(
        ContenidoEducativo,
        through='RutaAprendizajeContenido',
        related_name='rutas',
    )

    class Meta:
        ordering = ['id']
        verbose_name = 'ruta de aprendizaje'
        verbose_name_plural = 'rutas de aprendizaje'

    def __str__(self):
        return self.nombre


class RutaAprendizajeContenido(models.Model):
    """Tabla intermedia ordenada (el `idProceso` del diagrama ER)."""
    ruta = models.ForeignKey(RutaAprendizaje, on_delete=models.CASCADE, related_name='pasos')
    contenido = models.ForeignKey(ContenidoEducativo, on_delete=models.CASCADE)
    orden = models.PositiveSmallIntegerField()

    class Meta:
        ordering = ['ruta', 'orden']
        constraints = [
            models.UniqueConstraint(fields=['ruta', 'contenido'], name='ruta_contenido_unico'),
            models.UniqueConstraint(fields=['ruta', 'orden'], name='ruta_orden_unico'),
        ]

    def __str__(self):
        return f"{self.ruta} #{self.orden}: {self.contenido}"
