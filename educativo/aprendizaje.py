"""
Motor de aprendizaje: puntos, rachas, niveles e insignias por ruta.

Se llama desde las vistas cuando la usuaria marca un contenido como leído o
completa un ejercicio. Todo se calcula en el servidor con `request.user`; el
frontend solo muestra el resultado.
"""
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone

from .acceso import usuaria_es_premium

from .models import (
    InsigniaObtenida,
    InsigniaRuta,
    InteraccionContenido,
    MovimientoAprendizaje,
    NivelAprendizaje,
    ProgresoAprendizaje,
    ReglaAprendizaje,
)

# Racha alcanzada -> clave de la regla que da el bonus.
HITOS_RACHA = {3: 'racha_aprendizaje_3', 7: 'racha_aprendizaje_7', 30: 'racha_aprendizaje_30'}

# Con qué frecuencia puede dar puntos la misma acción sobre el mismo elemento.
# Por defecto, una vez al día (evita acumular puntos repitiendo sin parar).
SOLO_UNA_VEZ = {'contenido_leido', 'ruta_completada'}


# Zona horaria de las usuarias. El proyecto tiene TIME_ZONE = 'UTC' en
# settings.py; si se usara esa, el "día" de la racha cambiaría a las 7 p. m.
# hora Colombia. Con esta zona, el día cambia a medianoche en Colombia, igual
# que en Síntomas (que usa la fecha local del servidor). Si algún día el
# proyecto pasa a TIME_ZONE = 'America/Bogota', esto sigue dando lo mismo.
ZONA_USUARIAS = ZoneInfo('America/Bogota')


def _hoy():
    return timezone.localdate(timezone=ZONA_USUARIAS)


def _otorgar(usuario, clave, referencia, hoy):
    """
    Da los puntos de una regla. Devuelve los puntos ganados (0 si la regla no
    existe, está inactiva o ya se otorgó: una vez en la vida para
    `SOLO_UNA_VEZ`, una vez por día para el resto).
    """
    regla = ReglaAprendizaje.objects.filter(clave=clave, activa=True).first()
    if regla is None:
        return 0
    previos = MovimientoAprendizaje.objects.filter(
        usuario=usuario, clave=clave, referencia=referencia
    )
    if clave not in SOLO_UNA_VEZ:
        previos = previos.filter(fecha=hoy)
    if previos.exists():
        return 0
    MovimientoAprendizaje.objects.create(
        usuario=usuario,
        fecha=hoy,
        clave=clave,
        referencia=referencia,
        motivo=regla.descripcion,
        puntos=regla.puntos,
    )
    return regla.puntos


def nivel_para(puntos):
    """Devuelve (nivel_actual, nivel_siguiente); alguno puede ser None."""
    actual = None
    siguiente = None
    for nivel in NivelAprendizaje.objects.all():
        if nivel.puntos_minimos <= puntos:
            actual = nivel
        else:
            siguiente = nivel
            break
    return actual, siguiente


def racha_vigente(progreso, hoy=None):
    """La racha guardada deja de valer si se saltó un día."""
    hoy = hoy or _hoy()
    if progreso.ultimo_dia_activo is None or progreso.ultimo_dia_activo < hoy - timedelta(days=1):
        return 0
    return progreso.racha_actual


def progreso_de_ruta(usuario, ruta):
    """(completados, total) de los contenidos de una ruta."""
    ids = list(ruta.pasos.values_list('contenido_id', flat=True))
    if not ids:
        return 0, 0
    hechos = InteraccionContenido.objects.filter(
        usuario=usuario, completado=True, contenido_id__in=ids
    ).count()
    return hechos, len(ids)


def evaluar_insignias(usuario, hoy=None):
    """
    Entrega las insignias de las rutas que la usuaria ya completó y que aún
    no tiene. Cada una da además los puntos de `ruta_completada`. Devuelve
    (insignias_nuevas, puntos_ganados).
    """
    hoy = hoy or _hoy()
    ya = set(InsigniaObtenida.objects.filter(usuario=usuario).values_list('insignia_id', flat=True))
    nuevas = []
    puntos = 0
    for insignia in InsigniaRuta.objects.select_related('ruta').exclude(id__in=ya):
        hechos, total = progreso_de_ruta(usuario, insignia.ruta)
        if total and hechos == total:
            InsigniaObtenida.objects.create(usuario=usuario, insignia=insignia)
            puntos += _otorgar(usuario, 'ruta_completada', insignia.ruta_id, hoy)
            nuevas.append(insignia)
    return nuevas, puntos


def registrar_actividad_educativa(usuario, clave, referencia=''):
    """
    Se llama cada vez que la usuaria lee un contenido o completa un ejercicio:
    suma puntos si corresponde, actualiza la racha (cuenta días, no
    acciones), entrega insignias de ruta y calcula si subió de nivel.

    Devuelve un dict para que la app muestre la recompensa.
    """
    hoy = _hoy()
    progreso, _ = ProgresoAprendizaje.objects.get_or_create(usuario=usuario)
    nivel_antes, _ = nivel_para(progreso.puntos_totales)

    ganados = _otorgar(usuario, clave, referencia, hoy)

    if progreso.ultimo_dia_activo != hoy:
        if progreso.ultimo_dia_activo == hoy - timedelta(days=1):
            progreso.racha_actual += 1
        else:
            progreso.racha_actual = 1
        progreso.ultimo_dia_activo = hoy
        progreso.racha_maxima = max(progreso.racha_maxima, progreso.racha_actual)

        clave_hito = HITOS_RACHA.get(progreso.racha_actual)
        if clave_hito:
            ganados += _otorgar(usuario, clave_hito, '', hoy)

    nuevas, puntos_insignias = evaluar_insignias(usuario, hoy)
    ganados += puntos_insignias

    progreso.puntos_totales += ganados
    progreso.save()

    nivel_despues, _ = nivel_para(progreso.puntos_totales)
    subio = nivel_despues is not None and (nivel_antes is None or nivel_despues.id != nivel_antes.id)

    return {
        'puntos_ganados': ganados,
        'puntos_totales': progreso.puntos_totales,
        'racha_actual': progreso.racha_actual,
        'nivel': nivel_despues.nombre if nivel_despues else None,
        'subio_de_nivel': nivel_despues.nombre if subio else None,
        'insignias_nuevas': [
            {'id': i.id, 'nombre': i.nombre, 'emoji': i.emoji} for i in nuevas
        ],
    }


def resumen_progreso(usuario):
    """Todo lo que muestra la pantalla "Mi progreso" (GET /progreso/)."""
    hoy = _hoy()
    progreso, _ = ProgresoAprendizaje.objects.get_or_create(usuario=usuario)
    es_premium = usuaria_es_premium(usuario)

    # Pone al día las insignias de rutas ya completadas antes de que existiera
    # el motor (o editadas desde el admin).
    _, puntos = evaluar_insignias(usuario, hoy)
    if puntos:
        progreso.puntos_totales += puntos
        progreso.save()

    actual, siguiente = nivel_para(progreso.puntos_totales)
    if siguiente is not None:
        base = actual.puntos_minimos if actual else 0
        tramo = siguiente.puntos_minimos - base
        fraccion = (progreso.puntos_totales - base) / tramo if tramo else 1.0
    else:
        fraccion = 1.0

    obtenidas = {
        o.insignia_id: o.fecha
        for o in InsigniaObtenida.objects.filter(usuario=usuario)
    }
    insignias = []
    for insignia in InsigniaRuta.objects.select_related('ruta'):
        hechos, total = progreso_de_ruta(usuario, insignia.ruta)
        fecha = obtenidas.get(insignia.id)
        insignias.append({
            'id': insignia.id,
            'nombre': insignia.nombre,
            'descripcion': insignia.descripcion,
            'emoji': insignia.emoji,
            'ruta_id': insignia.ruta_id,
            'ruta_nombre': insignia.ruta.nombre,
            'obtenida': fecha is not None,
            'fecha_obtenida': (
                timezone.localtime(fecha, ZONA_USUARIAS).date().isoformat() if fecha else None
            ),
            'contenidos_completados': hechos,
            'contenidos_total': total,
            # Si la ruta tiene contenido premium y la usuaria es gratuita, no
            # puede completarla: la app se lo avisa.
            'requiere_premium': (
                not es_premium and insignia.ruta.contenidos.filter(es_premium=True).exists()
            ),
        })

    racha = racha_vigente(progreso, hoy)
    historial = MovimientoAprendizaje.objects.filter(usuario=usuario)[:15]

    return {
        'puntos_totales': progreso.puntos_totales,
        'nivel': {
            'nombre': actual.nombre if actual else None,
            'emoji': actual.emoji if actual else '',
            'puntos_minimos': actual.puntos_minimos if actual else 0,
        },
        'siguiente_nivel': {
            'nombre': siguiente.nombre,
            'emoji': siguiente.emoji,
            'puntos_minimos': siguiente.puntos_minimos,
        } if siguiente else None,
        'progreso_nivel': round(fraccion, 4),
        'racha_actual': racha,
        'racha_maxima': progreso.racha_maxima,
        'activa_hoy': progreso.ultimo_dia_activo == hoy,
        'insignias': insignias,
        # Cómo se ganan puntos (según las reglas activas del admin).
        'reglas': [
            {'clave': r.clave, 'descripcion': r.descripcion, 'puntos': r.puntos}
            for r in ReglaAprendizaje.objects.filter(activa=True)
        ],
        'historial': [
            {'fecha': m.fecha.isoformat(), 'motivo': m.motivo, 'puntos': m.puntos}
            for m in historial
        ],
    }
