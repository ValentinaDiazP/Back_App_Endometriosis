from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    CategoriaContenidoViewSet,
    ContenidoEducativoViewSet,
    EjercicioPsicoeducativoViewSet,
    InteraccionContenidoViewSet,
    PreferenciasView,
    RegistroEjercicioViewSet,
    RutaAprendizajeViewSet,
)

router = DefaultRouter()
# Catálogo (solo lectura)
router.register('categorias', CategoriaContenidoViewSet, basename='categoria-contenido')
router.register('contenidos', ContenidoEducativoViewSet, basename='contenido-educativo')
router.register('ejercicios', EjercicioPsicoeducativoViewSet, basename='ejercicio-psicoeducativo')
router.register('rutas', RutaAprendizajeViewSet, basename='ruta-aprendizaje')
# Datos de la usuaria
router.register('interacciones-contenido', InteraccionContenidoViewSet, basename='interaccion-contenido')
router.register('registros-ejercicio', RegistroEjercicioViewSet, basename='registro-ejercicio')

urlpatterns = [
    path('preferencias/', PreferenciasView.as_view(), name='preferencias'),
] + router.urls
