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
router.register(r'profesionales', ProfessionalViewSet, basename='professional')
router.register(r'citas', CitaMedicaViewSet, basename='citas')
router.register(r'publicaciones', PublicacionViewSet, basename='publicaciones')
router.register(r'comentarios', ComentarioViewSet, basename='comentarios')
router.register(r'solicitudes-contacto', SolicitudContactoViewSet, basename='solicitudes-contacto')
router.register(r'productos', ProductoViewSet, basename='productos')
router.register(r'carrito', CarritoViewSet, basename='carrito')
router.register(r'compras', ComprarViewSet, basename='compras')

urlpatterns = [
    path('', include(router.urls)),
]