from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ProfessionalViewSet,
    CitaMedicaViewSet,
    PublicacionViewSet,
    ComentarioViewSet,
    SolicitudContactoViewSet,
    ProductoViewSet,
    CarritoViewSet,
    ComprarViewSet,
)

router = DefaultRouter()
router.register(r'professionals', ProfessionalViewSet, basename='professional')
router.register(r'profesionales/citas', CitaMedicaViewSet, basename='profesionales-citas')
router.register(r'publicaciones', PublicacionViewSet, basename='publicaciones')
router.register(r'comentarios', ComentarioViewSet, basename='comentarios')
router.register(r'solicitudes-contacto', SolicitudContactoViewSet, basename='solicitudes-contacto')
router.register(r'bienestar/productos', ProductoViewSet, basename='bienestar-productos')
router.register(r'bienestar/carrito', CarritoViewSet, basename='bienestar-carrito')
router.register(r'bienestar/compras', ComprarViewSet, basename='bienestar-compras')

urlpatterns = [
    path('', include(router.urls)),
]