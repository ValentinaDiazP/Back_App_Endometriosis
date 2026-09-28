from django.contrib import admin
from .models import Professional, Publicacion, Comentario, MeGusta, ReportePublicacion

@admin.action(description='Aprobar publicaciones seleccionadas')
def aprobar_publicaciones(modeladmin, request, queryset):
    queryset.update(estado='APROBADO')

@admin.action(description='Rechazar publicaciones seleccionadas')
def rechazar_publicaciones(modeladmin, request, queryset):
    queryset.update(estado='RECHAZADO')

@admin.register(Publicacion)
class PublicacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'contenido_corto', 'estado', 'fecha_creacion')
    list_filter = ('estado', 'fecha_creacion')
    search_fields = ('contenido', 'usuario__username')
    actions = [aprobar_publicaciones, rechazar_publicaciones]

    def contenido_corto(self, obj):
        return obj.contenido[:50]

@admin.register(ReportePublicacion)
class ReportePublicacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'publicacion', 'usuario', 'motivo', 'resuelto', 'fecha_reporte')
    list_filter = ('resuelto', 'fecha_reporte')
    search_fields = ('motivo', 'usuario__username')

admin.site.register(Professional)
admin.site.register(Comentario)
admin.site.register(MeGusta)