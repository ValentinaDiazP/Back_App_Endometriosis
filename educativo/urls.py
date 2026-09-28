from rest_framework.routers import DefaultRouter

from .views import (
    CategoriaContenidoViewSet,
    ContenidoEducativoViewSet,
    EjercicioPsicoeducativoViewSet,
    RutaAprendizajeViewSet,
)

router = DefaultRouter()
router.register('categorias', CategoriaContenidoViewSet, basename='categoria-contenido')
router.register('contenidos', ContenidoEducativoViewSet, basename='contenido-educativo')
router.register('ejercicios', EjercicioPsicoeducativoViewSet, basename='ejercicio-psicoeducativo')
router.register('rutas', RutaAprendizajeViewSet, basename='ruta-aprendizaje')

urlpatterns = router.urls
