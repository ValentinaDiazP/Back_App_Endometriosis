from django.contrib import admin

from .models import (
    CategoriaContenido,
    ContenidoEducativo,
    EjercicioPsicoeducativo,
    InteraccionContenido,
    PreferenciaUsuario,
    RegistroEjercicio,
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
    list_display = ['id', 'nombre', 'tipo', 'minutos_estimados', 'tiene_enlace']
    list_filter = ['tipo']

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
