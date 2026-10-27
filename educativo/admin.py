from django.contrib import admin

from .models import (
    CategoriaContenido,
    ContenidoEducativo,
    EjercicioPsicoeducativo,
    InsigniaObtenida,
    InsigniaRuta,
    InteraccionContenido,
    MovimientoAprendizaje,
    NivelAprendizaje,
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


@admin.register(ContenidoEducativo)
class ContenidoEducativoAdmin(admin.ModelAdmin):
    list_display = ['id', 'titulo', 'categoria', 'tipo', 'nivel', 'es_premium', 'fecha_publicacion', 'tiene_enlace']
    list_filter = ['categoria', 'tipo', 'nivel', 'es_premium']
    search_fields = ['titulo', 'resumen']

    @admin.display(boolean=True, description='¿Tiene enlace?')
    def tiene_enlace(self, obj):
        return bool(obj.url_recurso)


@admin.register(EjercicioPsicoeducativo)
class EjercicioPsicoeducativoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'tipo', 'minutos_estimados', 'es_premium', 'tiene_enlace']
    list_filter = ['tipo', 'es_premium']

    @admin.display(boolean=True, description='¿Tiene enlace?')
    def tiene_enlace(self, obj):
        return bool(obj.url_recurso)


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
