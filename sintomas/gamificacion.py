from datetime import date, timedelta

from .models import Gamificacion, MovimientoPuntos, ReglaPuntos

# Racha alcanzada -> clave de la regla que da el bonus.
HITOS_RACHA = {7: 'racha_7', 30: 'racha_30', 90: 'racha_90'}


def _otorgar(usuario, clave, hoy):
    """
    Da los puntos de una regla, pero solo una vez por día y por clave
    (evita acumular puntos registrando muchas veces seguidas).
    Devuelve los puntos ganados (0 si la regla no existe, está inactiva
    o ya se otorgó hoy).
    """
    regla = ReglaPuntos.objects.filter(clave=clave, activa=True).first()
    if regla is None:
        return 0
    if MovimientoPuntos.objects.filter(usuario=usuario, fecha=hoy, clave=clave).exists():
        return 0
    MovimientoPuntos.objects.create(
        usuario=usuario,
        fecha=hoy,
        clave=clave,
        motivo=regla.descripcion,
        puntos=regla.puntos,
    )
    return regla.puntos


def registrar_actividad(usuario, clave):
    """
    Se llama cada vez que la usuaria guarda un registro (síntomas, ánimo,
    ciclo): suma puntos si corresponde y actualiza la racha. La racha
    cuenta días, no registros: solo cambia la primera vez que hay
    actividad en el día.
    """
    hoy = date.today()
    gami, _ = Gamificacion.objects.get_or_create(usuario=usuario)

    ganados = _otorgar(usuario, clave, hoy)

    if gami.ultimo_dia_activo != hoy:
        if gami.ultimo_dia_activo == hoy - timedelta(days=1):
            gami.racha_actual += 1
        else:
            gami.racha_actual = 1
        gami.ultimo_dia_activo = hoy
        gami.racha_maxima = max(gami.racha_maxima, gami.racha_actual)

        clave_hito = HITOS_RACHA.get(gami.racha_actual)
        if clave_hito:
            ganados += _otorgar(usuario, clave_hito, hoy)

    gami.puntos_totales += ganados
    gami.save()
    return gami