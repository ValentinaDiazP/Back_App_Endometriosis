from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    GamificacionView,
    LocalizacionDolorViewSet,
    RegistroCicloViewSet,
    RegistroEmocionalViewSet,
    RegistroSintomaViewSet,
    SintomaAsociadoViewSet,
    RegistroCicloViewSet,
)

router = DefaultRouter()
router.register('localizaciones-dolor', LocalizacionDolorViewSet, basename='localizacion-dolor')
router.register('sintomas-asociados', SintomaAsociadoViewSet, basename='sintoma-asociado')
router.register('registros-sintoma', RegistroSintomaViewSet, basename='registro-sintoma')
router.register('registros-emocionales', RegistroEmocionalViewSet, basename='registro-emocional')
router.register('registros-ciclo', RegistroCicloViewSet, basename='registro-ciclo')

urlpatterns = router.urls + [
    path('gamificacion/', GamificacionView.as_view(), name='gamificacion'),
]