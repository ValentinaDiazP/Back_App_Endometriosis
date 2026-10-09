from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.http import require_POST
from .models import Publicacion, Comentario, ReportePublicacion, Professional

def es_moderador(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name='Moderador').exists() or user.is_staff)

@user_passes_test(es_moderador, login_url='/admin/login/')
def dashboard_moderacion(view_request):
    # Solo reportes pendientes (resuelto=False)
    reportes_pendientes = ReportePublicacion.objects.select_related(
        'publicacion', 'publicacion__usuario', 'usuario'
    ).filter(resuelto=False)

    profesionales = Professional.objects.all()

    context = {
        'publicaciones_reportadas': reportes_pendientes,
        'comentarios_reportados': [], # Espacio reservado para reportes de comentarios si aplica
        'profesionales': profesionales,
    }
    return render(view_request, 'moderacion/dashboard.html', context)

@require_POST
@user_passes_test(es_moderador, login_url='/admin/login/')
def resolver_reporte(view_request, reporte_id):
    reporte = get_object_or_404(ReportePublicacion, id=reporte_id)
    accion = view_request.POST.get('accion')
    
    pub = reporte.publicacion
    if accion == 'aprobar':
        # Ocultar / Rechazar la publicación
        pub.estado = 'RECHAZADO'
        pub.save()
        reporte.resuelto = True
        reporte.save()
    elif accion == 'descartar':
        # Mantener aprobada o conservar visible
        pub.estado = 'APROBADO'
        pub.save()
        reporte.resuelto = True
        reporte.save()
        
    return redirect('/moderacion/')
