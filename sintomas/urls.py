from rest_framework.routers import DefaultRouter

from .views import (
    LocalizacionDolorViewSet,
    RegistroEmocionalViewSet,
    RegistroSintomaViewSet,
    SintomaAsociadoViewSet,
)

router = DefaultRouter()
router.register('localizaciones-dolor', LocalizacionDolorViewSet, basename='localizacion-dolor')
router.register('sintomas-asociados', SintomaAsociadoViewSet, basename='sintoma-asociado')
router.register('registros-sintoma', RegistroSintomaViewSet, basename='registro-sintoma')
router.register('registros-emocionales', RegistroEmocionalViewSet, basename='registro-emocional')

urlpatterns = router.urls