from django.conf import settings
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
    # Opcional: enlace al video o podcast (YouTube, Spotify, etc.). La app
    # muestra un botón para abrirlo fuera de Florecer.
    url_recurso = models.URLField(max_length=500, blank=True)

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
    # Opcional: audio o video guiado externo (YouTube, Spotify, etc.).
    url_recurso = models.URLField(max_length=500, blank=True)
    # Solo para usuarias con plan premium u hospital (ver educativo/acceso.py).
    es_premium = models.BooleanField(default=False)

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


# ---------------------------------------------------------------------------
# Datos de cada usuaria. Siempre se filtran por request.user en las vistas;
# el frontend nunca envía el id de la usuaria.
# ---------------------------------------------------------------------------


class PreferenciaUsuario(models.Model):
    """Categorías que la usuaria eligió en el onboarding o en 'Mis preferencias'."""
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='preferencias_educativas',
    )
    categoria = models.ForeignKey(CategoriaContenido, on_delete=models.CASCADE)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'categoria'], name='preferencia_unica'),
        ]
        verbose_name = 'preferencia de usuaria'
        verbose_name_plural = 'preferencias de usuarias'

    def __str__(self):
        return f"{self.usuario.username} → {self.categoria}"


class InteraccionContenido(models.Model):
    """Una fila por usuaria y contenido; se crea al marcarlo como leído."""
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='interacciones_contenido',
    )
    contenido = models.ForeignKey(ContenidoEducativo, on_delete=models.CASCADE)
    completado = models.BooleanField(default=True)
    fecha = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha']
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'contenido'], name='interaccion_unica'),
        ]
        verbose_name = 'interacción con contenido'
        verbose_name_plural = 'interacciones con contenido'

    def __str__(self):
        return f"{self.usuario.username} - {self.contenido}"


class RegistroEjercicio(models.Model):
    """Cada vez que la usuaria completa un ejercicio (puede repetirlo)."""
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='registros_ejercicio',
    )
    ejercicio = models.ForeignKey(EjercicioPsicoeducativo, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    # Opcionales: la pantalla actual aún no los pide.
    respuestas = models.TextField(blank=True)
    utilidad = models.PositiveSmallIntegerField(null=True, blank=True)  # 1 a 5

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'registro de ejercicio'
        verbose_name_plural = 'registros de ejercicio'

    def __str__(self):
        return f"{self.usuario.username} - {self.ejercicio} ({self.fecha:%Y-%m-%d})"


class PreguntaFrecuente(models.Model):
    class Categoria(models.TextChoices):
        MANEJO_DOLOR = 'Manejo del Dolor / Brotes', 'Manejo del Dolor / Brotes'
        ESTILO_VIDA = 'Estilo de Vida y Nutrición', 'Estilo de Vida y Nutrición'
        TRATAMIENTOS = 'Tratamientos y Medicación', 'Tratamientos y Medicación'
        BIENESTAR_EMOCIONAL = 'Bienestar Emocional', 'Bienestar Emocional'

    pregunta = models.CharField(max_length=300)
    respuesta = models.TextField()
    categoria = models.CharField(max_length=50, choices=Categoria.choices)
    articulo_relacionado = models.ForeignKey(
        ContenidoEducativo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='preguntas_frecuentes',
    )

    class Meta:
        ordering = ['categoria', 'pregunta']
        verbose_name = 'pregunta frecuente'
        verbose_name_plural = 'preguntas frecuentes'

    def __str__(self):
        return self.pregunta


# ---------------------------------------------------------------------------
# Motor de aprendizaje (gamificación del módulo Educativo): puntos, niveles,
# rachas de aprendizaje e insignias por ruta. Es independiente de la
# gamificación de Seguimiento (sintomas.Gamificacion): aquí solo cuentan las
# acciones educativas. Las reglas, niveles e insignias se editan desde el admin.
# ---------------------------------------------------------------------------


class ReglaAprendizaje(models.Model):
    """Cuántos puntos da cada acción educativa. Editable desde /admin/."""
    clave = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=150)
    puntos = models.PositiveIntegerField()
    activa = models.BooleanField(default=True)

    class Meta:
        ordering = ['clave']
        verbose_name = 'regla de puntos de aprendizaje'
        verbose_name_plural = 'reglas de puntos de aprendizaje'

    def __str__(self):
        return f"{self.clave}: {self.puntos} pts"


class NivelAprendizaje(models.Model):
    """Umbrales de los niveles de progreso educativo. Editable desde /admin/."""
    nombre = models.CharField(max_length=50)
    puntos_minimos = models.PositiveIntegerField(unique=True)
    emoji = models.CharField(max_length=8, blank=True)

    class Meta:
        ordering = ['puntos_minimos']
        verbose_name = 'nivel de aprendizaje'
        verbose_name_plural = 'niveles de aprendizaje'

    def __str__(self):
        return f"{self.nombre} (desde {self.puntos_minimos} pts)"


class InsigniaRuta(models.Model):
    """Insignia que se gana al completar todos los contenidos de una ruta."""
    ruta = models.OneToOneField(RutaAprendizaje, on_delete=models.CASCADE, related_name='insignia')
    nombre = models.CharField(max_length=100)
    descripcion = models.CharField(max_length=200, blank=True)
    emoji = models.CharField(max_length=8, blank=True)

    class Meta:
        ordering = ['ruta']
        verbose_name = 'insignia de ruta'
        verbose_name_plural = 'insignias de ruta'

    def __str__(self):
        return f"{self.nombre} ({self.ruta})"


class ProgresoAprendizaje(models.Model):
    """Totales de cada usuaria: puntos y racha de aprendizaje."""
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='progreso_aprendizaje',
    )
    puntos_totales = models.PositiveIntegerField(default=0)
    racha_actual = models.PositiveIntegerField(default=0)
    racha_maxima = models.PositiveIntegerField(default=0)
    ultimo_dia_activo = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'progreso de aprendizaje'
        verbose_name_plural = 'progresos de aprendizaje'

    def __str__(self):
        return f"{self.usuario.username}: {self.puntos_totales} pts, racha {self.racha_actual}"


class MovimientoAprendizaje(models.Model):
    """Historial: una fila por cada vez que la usuaria ganó puntos."""
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='movimientos_aprendizaje',
    )
    fecha = models.DateField()
    clave = models.CharField(max_length=50)
    # Id del contenido, ejercicio o ruta que originó los puntos.
    referencia = models.CharField(max_length=50, blank=True)
    motivo = models.CharField(max_length=150)
    puntos = models.PositiveIntegerField()
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-creado_en']
        verbose_name = 'movimiento de puntos de aprendizaje'
        verbose_name_plural = 'movimientos de puntos de aprendizaje'

    def __str__(self):
        return f"{self.usuario.username} +{self.puntos} ({self.motivo})"


class InsigniaObtenida(models.Model):
    """Una fila por usuaria e insignia ganada."""
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='insignias_obtenidas',
    )
    insignia = models.ForeignKey(InsigniaRuta, on_delete=models.CASCADE, related_name='obtenidas')
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        constraints = [
            models.UniqueConstraint(fields=['usuario', 'insignia'], name='insignia_obtenida_unica'),
        ]
        verbose_name = 'insignia obtenida'
        verbose_name_plural = 'insignias obtenidas'

    def __str__(self):
        return f"{self.usuario.username} - {self.insignia.nombre}"
