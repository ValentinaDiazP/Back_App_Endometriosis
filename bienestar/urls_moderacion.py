from django.urls import path
from .views_moderacion import dashboard_moderacion, resolver_reporte

urlpatterns = [
    path('', dashboard_moderacion, name='dashboard_moderacion'),
    path('resolver/<int:reporte_id>/', resolver_reporte, name='resolver_reporte'),
]
