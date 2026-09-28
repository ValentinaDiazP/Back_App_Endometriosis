from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProfessionalViewSet, PublicacionViewSet, ComentarioViewSet

router = DefaultRouter()
router.register(r'professionals', ProfessionalViewSet, basename='professional')
router.register(r'publicaciones', PublicacionViewSet, basename='publicaciones')
router.register(r'comentarios', ComentarioViewSet, basename='comentarios')

urlpatterns = [
    path('', include(router.urls)),
]