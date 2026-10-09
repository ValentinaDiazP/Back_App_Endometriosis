from django.contrib import admin
from .models import Professional, Publicacion, Comentario, MeGusta, ReportePublicacion, SolicitudContacto


@admin.action(description='Aprobar publicaciones')
def aprobar_publicaciones(modeladmin, request, queryset):
    queryset.update(estado='APROBADO')


@admin.action(description='Ocultar publicaciones')
def ocultar_publicaciones(modeladmin, request, queryset):
    queryset.update(estado='RECHAZADO')


@admin.register(Professional)
class ProfessionalAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'specialty', 'rate', 'availability', 'whatsapp')
    search_fields = ('name', 'specialty')
    list_filter = ('specialty', 'availability')


@admin.register(Publicacion)
class PublicacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'contenido_corto', 'usuario', 'es_anonimo', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'es_anonimo', 'fecha_creacion')
    search_fields = ('contenido', 'usuario__username')
    readonly_fields = ('usuario', 'fecha_creacion')
    actions = [aprobar_publicaciones, ocultar_publicaciones]

    @admin.display(description='Contenido corto')
    def contenido_corto(self, obj):
        if not obj.contenido:
            return ''
        return obj.contenido[:50] + ('…' if len(obj.contenido) > 50 else '')


@admin.register(ReportePublicacion)
class ReportePublicacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'publicacion', 'motivo_corto', 'usuario', 'resuelto', 'fecha_reporte')
    list_filter = ('resuelto', 'fecha_reporte')
    search_fields = ('motivo', 'usuario__username', 'publicacion__contenido')
    list_select_related = ('publicacion', 'usuario')
    raw_id_fields = ('publicacion', 'usuario')

    @admin.display(description='Motivo')
    def motivo_corto(self, obj):
        if not obj.motivo:
            return ''
        return obj.motivo[:80] + ('…' if len(obj.motivo) > 80 else '')


@admin.register(SolicitudContacto)
class SolicitudContactoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'profesional', 'estado', 'fecha_solicitud')
    list_filter = ('estado', 'fecha_solicitud')
    search_fields = ('usuario__username', 'profesional__name')


@admin.register(Comentario)
class ComentarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'publicacion', 'usuario', 'texto_corto', 'fecha_creacion')
    search_fields = ('texto', 'usuario__username')

    @admin.display(description='Texto')
    def texto_corto(self, obj):
        if not obj.texto:
            return ''
        return obj.texto[:50] + ('…' if len(obj.texto) > 50 else '')


@admin.register(MeGusta)
class MeGustaAdmin(admin.ModelAdmin):
    list_display = ('id', 'publicacion', 'usuario', 'fecha')
