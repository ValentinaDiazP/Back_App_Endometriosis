from django.contrib import admin
from django.utils.html import format_html

from .models import (
    CategoriaContenido,
    ContenidoEducativo,
    EjercicioPsicoeducativo,
    InsigniaObtenida,
    InsigniaRuta,
    IndicacionPractica,
    InteraccionContenido,
    MovimientoAprendizaje,
    NivelAprendizaje,
    PasoModuloGuiado,
    PreguntaFrecuente,
    PreferenciaUsuario,
    ProgresoAprendizaje,
    RegistroEjercicio,
    ReglaAprendizaje,
    RutaAprendizaje,
    RutaAprendizajeContenido,
)


@admin.register(CategoriaContenido)
class CategoriaContenidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre']


def _ayuda_id(form, texto):
    """Pone una ayuda al campo `id` (código de texto) al crear un registro."""
    if 'id' in form.base_fields:
        form.base_fields['id'].help_text = texto
    return form


@admin.register(ContenidoEducativo)
class ContenidoEducativoAdmin(admin.ModelAdmin):
    """Gestor de contenidos: textos, enlaces e imágenes de la Biblioteca."""
    list_display = [
        'id', 'titulo', 'categoria', 'tipo', 'nivel', 'es_premium',
        'fecha_publicacion', 'tiene_enlace', 'tiene_imagen',
    ]
    list_filter = ['categoria', 'tipo', 'nivel', 'es_premium']
    search_fields = ['titulo', 'resumen', 'cuerpo']
    list_per_page = 25
    readonly_fields = ['vista_previa_imagen']
    fieldsets = [
        ('Información general', {
            'fields': ['id', 'titulo', 'categoria', ('tipo', 'nivel'), 'fecha_publicacion',
                       'minutos_estimados', 'es_premium'],
        }),
        ('Texto', {
            'description': 'El resumen se ve en las tarjetas; el cuerpo, al abrir el contenido.',
            'fields': ['resumen', 'cuerpo'],
        }),
        ('Video, audio e imagen', {
            'description': 'Todo es opcional. El enlace puede ser de YouTube, Spotify u otro sitio.',
            'fields': ['url_recurso', 'imagen', 'pie_de_imagen', 'vista_previa_imagen'],
        }),
    ]

    def get_readonly_fields(self, request, obj=None):
        # El código (id) no se cambia después de crear el contenido.
        return ['id', *self.readonly_fields] if obj else self.readonly_fields

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return _ayuda_id(form, 'Código único, por ejemplo c5. No se puede cambiar después.')

    @admin.display(boolean=True, description='¿Tiene enlace?')
    def tiene_enlace(self, obj):
        return bool(obj.url_recurso)

    @admin.display(boolean=True, description='¿Tiene imagen?')
    def tiene_imagen(self, obj):
        return bool(obj.imagen)

    @admin.display(description='Vista previa')
    def vista_previa_imagen(self, obj):
        if obj and obj.imagen:
            return format_html('<img src="{}" style="max-height:160px;border-radius:8px">', obj.imagen.url)
        return 'Sin imagen'


class PasoModuloGuiadoInline(admin.StackedInline):
    model = PasoModuloGuiado
    extra = 0
    ordering = ['orden', 'id']
    verbose_name = 'paso del módulo guiado'
    verbose_name_plural = 'Pasos del módulo guiado (solo para ejercicios de psicoeducación)'
    fields = [('orden', 'titulo'), 'texto', 'punto_clave']


class IndicacionPracticaInline(admin.TabularInline):
    model = IndicacionPractica
    extra = 0
    ordering = ['orden', 'id']
    verbose_name = 'indicación'
    verbose_name_plural = 'Indicaciones de la práctica guiada (solo para ACT y Mindfulness)'


@admin.register(EjercicioPsicoeducativo)
class EjercicioPsicoeducativoAdmin(admin.ModelAdmin):
    """
    Gestor de ejercicios. Los de psicoeducación llevan sus pasos aquí mismo; los
    de ACT/Mindfulness, sus indicaciones. Los ejercicios interactivos de TCC y
    los de catastrofización y valores tienen su pantalla propia en la app.
    """
    list_display = ['id', 'nombre', 'tipo', 'minutos_estimados', 'es_premium', 'tiene_enlace',
                    'num_pasos', 'num_indicaciones']
    list_filter = ['tipo', 'es_premium']
    search_fields = ['nombre', 'descripcion']
    inlines = [PasoModuloGuiadoInline, IndicacionPracticaInline]

    def get_readonly_fields(self, request, obj=None):
        return ['id'] if obj else []

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return _ayuda_id(form, 'Código único, por ejemplo e9. No se puede cambiar después.')

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('pasos_modulo', 'indicaciones')

    @admin.display(boolean=True, description='¿Tiene enlace?')
    def tiene_enlace(self, obj):
        return bool(obj.url_recurso)

    @admin.display(description='Pasos')
    def num_pasos(self, obj):
        return len(obj.pasos_modulo.all())

    @admin.display(description='Indicaciones')
    def num_indicaciones(self, obj):
        return len(obj.indicaciones.all())


class RutaAprendizajeContenidoInline(admin.TabularInline):
    model = RutaAprendizajeContenido
    extra = 1
    ordering = ['orden']


@admin.register(RutaAprendizaje)
class RutaAprendizajeAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre']
    inlines = [RutaAprendizajeContenidoInline]


@admin.register(PreferenciaUsuario)
class PreferenciaUsuarioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'categoria']
    list_filter = ['categoria']


@admin.register(InteraccionContenido)
class InteraccionContenidoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'contenido', 'completado', 'fecha']
    list_filter = ['completado', 'contenido']


@admin.register(RegistroEjercicio)
class RegistroEjercicioAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'ejercicio', 'fecha', 'utilidad']
    list_filter = ['ejercicio']


@admin.register(PreguntaFrecuente)
class PreguntaFrecuenteAdmin(admin.ModelAdmin):
    list_display = ['pregunta', 'categoria', 'articulo_relacionado']
    list_filter = ['categoria']
    search_fields = ['pregunta', 'respuesta']


# --- Motor de aprendizaje -------------------------------------------------


@admin.register(ReglaAprendizaje)
class ReglaAprendizajeAdmin(admin.ModelAdmin):
    list_display = ['clave', 'descripcion', 'puntos', 'activa']
    list_editable = ['puntos', 'activa']


@admin.register(NivelAprendizaje)
class NivelAprendizajeAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'emoji', 'puntos_minimos']


@admin.register(InsigniaRuta)
class InsigniaRutaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'emoji', 'ruta']


@admin.register(ProgresoAprendizaje)
class ProgresoAprendizajeAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'puntos_totales', 'racha_actual', 'racha_maxima', 'ultimo_dia_activo']


@admin.register(MovimientoAprendizaje)
class MovimientoAprendizajeAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'fecha', 'clave', 'referencia', 'puntos']
    list_filter = ['clave']


@admin.register(InsigniaObtenida)
class InsigniaObtenidaAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'insignia', 'fecha']
    list_filter = ['insignia']
