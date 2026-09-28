"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/bienestar/', include('bienestar.urls')),   # Tu módulo     # Compañera 3
    path('api/usuarios/', include('usuarios.urls')),
    # Comentados hasta que tus compañeras creen sus apps y archivos urls.py:
    path('api/sintomas/', include('sintomas.urls')),  
    # path('api/reportes/', include('reportes.urls')),     
    path('api/educativo/', include('educativo.urls')),
]
# Servir archivos de imagen subidos localmente
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

