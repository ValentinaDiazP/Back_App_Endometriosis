from django.contrib import admin

from .models import (
    Gamificacion,
    LocalizacionDolor,
    MovimientoPuntos,
    NivelGamificacion,
    RegistroCiclo,
    RegistroEmocional,
    RegistroSintoma,
    ReglaPuntos,
    SintomaAsociado,
)

admin.site.register(LocalizacionDolor)
admin.site.register(SintomaAsociado)
admin.site.register(RegistroSintoma)
admin.site.register(RegistroEmocional)
admin.site.register(RegistroCiclo)
admin.site.register(ReglaPuntos)
admin.site.register(NivelGamificacion)
admin.site.register(Gamificacion)
admin.site.register(MovimientoPuntos)