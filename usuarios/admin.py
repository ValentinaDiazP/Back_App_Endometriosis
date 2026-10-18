from django.contrib import admin
from .models import PerfilUsuaria


@admin.register(PerfilUsuaria)
class PerfilUsuariaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'plan', 'onboarding_completado')
    list_filter = ('plan',)