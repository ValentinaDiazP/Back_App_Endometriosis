from rest_framework.routers import DefaultRouter

from .views import (
    LocalizacionDolorViewSet,
    RegistroSintomaViewSet,
    SintomaAsociadoViewSet,
)

router = DefaultRouter()
router.register('localizaciones-dolor', LocalizacionDolorViewSet, basename='localizacion-dolor')
router.register('sintomas-asociados', SintomaAsociadoViewSet, basename='sintoma-asociado')
router.register('registros-sintoma', RegistroSintomaViewSet, basename='registro-sintoma')

urlpatterns = router.urls