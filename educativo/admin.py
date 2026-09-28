from django.contrib import admin

from .models import (
    CategoriaContenido,
    ContenidoEducativo,
    EjercicioPsicoeducativo,
    RutaAprendizaje,
    RutaAprendizajeContenido,
)


@admin.register(CategoriaContenido)
class CategoriaContenidoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre']


@admin.register(ContenidoEducativo)
class ContenidoEducativoAdmin(admin.ModelAdmin):
    list_display = ['id', 'titulo', 'categoria', 'tipo', 'nivel', 'es_premium', 'fecha_publicacion']
    list_filter = ['categoria', 'tipo', 'nivel', 'es_premium']
    search_fields = ['titulo', 'resumen']


@admin.register(EjercicioPsicoeducativo)
class EjercicioPsicoeducativoAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'tipo', 'minutos_estimados']
    list_filter = ['tipo']


class RutaAprendizajeContenidoInline(admin.TabularInline):
    model = RutaAprendizajeContenido
    extra = 1
    ordering = ['orden']


@admin.register(RutaAprendizaje)
class RutaAprendizajeAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre']
    inlines = [RutaAprendizajeContenidoInline]
