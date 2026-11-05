"""
Recomendaciones automáticas del módulo Educativo.

Cruza tres fuentes para ordenar contenidos y ejercicios de cada usuaria:

1. Sus temas de interés (PreferenciaUsuario).
2. Sus datos de Seguimiento de los últimos 7 días (app `sintomas`):
   intensidad del dolor, check-in de ánimo y si está en su periodo.
3. Lo que ya completó (InteraccionContenido / RegistroEjercicio).

Lo premium sigue apareciendo para las usuarias gratuitas, pero más abajo y
marcado como bloqueado (ver educativo/acceso.py).
"""
from datetime import datetime, time, timedelta

from django.db.models import Avg, Count, Max

from sintomas.models import RegistroCiclo, RegistroEmocional, RegistroSintoma

from .acceso import esta_bloqueado
from .aprendizaje import ZONA_USUARIAS, _hoy
from .models import (
    ContenidoEducativo,
    EjercicioPsicoeducativo,
    InteraccionContenido,
    PreferenciaUsuario,
    RegistroEjercicio,
)

DIAS_VENTANA = 7
DOLOR_ALTO_PROMEDIO = 6     # escala 0-10
DOLOR_ALTO_PICO = 8         # un solo día así ya cuenta como semana de dolor alto
ANIMO_BAJO_PROMEDIO = 2.5   # escala 1-5 (1 = muy bajo, 3 = estable)
ANIMO_BUENO_PROMEDIO = 3.5
DIAS_PERIODO_SIN_FIN = 7    # si registró el inicio del periodo pero no el fin

CAT_ENDOMETRIOSIS = 'cat_endometriosis'
CAT_DOLOR = 'cat_dolor'
CAT_AUTOCUIDADO = 'cat_autocuidado'

MOTIVO_DOLOR = 'Registraste dolor alto esta semana'
MOTIVO_ANIMO = 'Tu ánimo ha estado bajo esta semana'
MOTIVO_PERIODO = 'Estás en tu periodo'

ORDEN_NIVEL = {'basico': 0, 'intermedio': 1, 'avanzado': 2}


def _formato_numero(valor):
    return f'{valor:.0f}' if valor == int(valor) else f'{valor:.1f}'


def senales_seguimiento(usuario, hoy=None):
    """Resumen de dolor, ánimo y ciclo de la usuaria en los últimos 7 días."""
    hoy = hoy or _hoy()
    desde = hoy - timedelta(days=DIAS_VENTANA - 1)
    inicio = datetime.combine(desde, time.min, tzinfo=ZONA_USUARIAS)

    dolor = RegistroSintoma.objects.filter(usuario=usuario, fecha_hora__gte=inicio).aggregate(
        promedio=Avg('intensidad_dolor'), maximo=Max('intensidad_dolor'), registros=Count('id')
    )
    animo = RegistroEmocional.objects.filter(usuario=usuario, fecha__gte=desde).aggregate(
        promedio=Avg('estado_animo'), registros=Count('id')
    )
    ciclo = RegistroCiclo.objects.filter(usuario=usuario, fecha_inicio__lte=hoy).order_by('-fecha_inicio').first()

    en_periodo = False
    if ciclo is not None:
        if ciclo.fecha_fin is not None:
            en_periodo = ciclo.fecha_fin >= hoy
        else:
            en_periodo = (hoy - ciclo.fecha_inicio).days < DIAS_PERIODO_SIN_FIN

    dolor_promedio = round(dolor['promedio'], 1) if dolor['registros'] else None
    animo_promedio = round(animo['promedio'], 1) if animo['registros'] else None
    dolor_alto = bool(dolor['registros']) and (
        dolor['promedio'] >= DOLOR_ALTO_PROMEDIO or dolor['maximo'] >= DOLOR_ALTO_PICO
    )
    animo_bajo = bool(animo['registros']) and animo['promedio'] <= ANIMO_BAJO_PROMEDIO

    partes = []
    if dolor_promedio is not None:
        partes.append(f'Dolor promedio {_formato_numero(dolor_promedio)}/10')
    if animo_promedio is not None:
        if animo_bajo:
            partes.append('ánimo bajo')
        elif animo_promedio >= ANIMO_BUENO_PROMEDIO:
            partes.append('ánimo bueno')
        else:
            partes.append('ánimo estable')
    if en_periodo:
        partes.append('en tu periodo')
    resumen = ' · '.join(partes)
    if resumen:
        resumen = resumen[0].upper() + resumen[1:]

    return {
        'dias_ventana': DIAS_VENTANA,
        'hay_datos': bool(partes),
        'resumen': resumen,
        'dolor_promedio': dolor_promedio,
        'dolor_maximo': dolor['maximo'],
        'registros_dolor': dolor['registros'],
        'dolor_alto': dolor_alto,
        'animo_promedio': animo_promedio,
        'registros_animo': animo['registros'],
        'animo_bajo': animo_bajo,
        'en_periodo': en_periodo,
    }


def _resultado(item_id, puntaje, motivos, completado, bloqueado):
    return {
        'id': item_id,
        'puntaje': puntaje,
        'motivo': ' · '.join(motivos) if motivos else None,
        'completado': completado,
        'bloqueado': bloqueado,
    }


def _puntuar_contenido(contenido, preferidas, senales, completados, es_premium):
    puntaje, motivos = 0, []
    if contenido.categoria_id in preferidas:
        puntaje += 3
        motivos.append(f'Porque te interesa {contenido.categoria.nombre}')
    if senales['dolor_alto'] and contenido.categoria_id == CAT_DOLOR:
        puntaje += 3
        motivos.append(MOTIVO_DOLOR)
    if senales['animo_bajo'] and contenido.categoria_id == CAT_AUTOCUIDADO:
        puntaje += 3
        motivos.append(MOTIVO_ANIMO)
    if senales['en_periodo'] and contenido.categoria_id in (CAT_DOLOR, CAT_AUTOCUIDADO):
        puntaje += 1
        motivos.append(MOTIVO_PERIODO)

    completado = contenido.id in completados
    bloqueado = esta_bloqueado(contenido, es_premium)
    if completado:
        puntaje -= 10  # lo ya leído baja al final (incluso detrás de lo bloqueado)
    if bloqueado:
        puntaje -= 2
    return _resultado(contenido.id, puntaje, motivos, completado, bloqueado)


def _puntuar_ejercicio(ejercicio, preferidas, senales, hechos, es_premium):
    tipo = ejercicio.tipo
    puntaje, motivos = 0, []
    if senales['dolor_alto'] and tipo in ('tcc', 'psicoeducacion'):
        puntaje += 3
        motivos.append(MOTIVO_DOLOR)
    if senales['animo_bajo'] and tipo == 'actMindfulness':
        puntaje += 3
        motivos.append(MOTIVO_ANIMO)
    if senales['en_periodo'] and tipo == 'actMindfulness':
        puntaje += 1
        motivos.append(MOTIVO_PERIODO)
    # Los temas de interés también orientan el enfoque del ejercicio.
    if CAT_DOLOR in preferidas and tipo == 'tcc':
        puntaje += 1
    if CAT_AUTOCUIDADO in preferidas and tipo == 'actMindfulness':
        puntaje += 1
    if CAT_ENDOMETRIOSIS in preferidas and tipo == 'psicoeducacion':
        puntaje += 1

    completado = ejercicio.id in hechos
    bloqueado = esta_bloqueado(ejercicio, es_premium)
    if completado:
        puntaje -= 2  # los ejercicios se pueden repetir: bajan menos que un contenido leído
    if bloqueado:
        puntaje -= 2
    return _resultado(ejercicio.id, puntaje, motivos, completado, bloqueado)


def recomendaciones_para(usuario, es_premium, hoy=None):
    """Todo lo que usa la pestaña "Para ti" (GET /recomendaciones/)."""
    senales = senales_seguimiento(usuario, hoy)
    preferidas = set(
        PreferenciaUsuario.objects.filter(usuario=usuario).values_list('categoria_id', flat=True)
    )
    leidos = set(
        InteraccionContenido.objects.filter(usuario=usuario, completado=True)
        .values_list('contenido_id', flat=True)
    )
    hechos = set(RegistroEjercicio.objects.filter(usuario=usuario).values_list('ejercicio_id', flat=True))

    contenidos = [
        (c, _puntuar_contenido(c, preferidas, senales, leidos, es_premium))
        for c in ContenidoEducativo.objects.select_related('categoria')
    ]
    contenidos.sort(key=lambda par: (-par[1]['puntaje'], ORDEN_NIVEL.get(par[0].nivel, 9), par[0].id))

    ejercicios = [
        _puntuar_ejercicio(e, preferidas, senales, hechos, es_premium)
        for e in EjercicioPsicoeducativo.objects.all()
    ]
    ejercicios.sort(key=lambda r: (-r['puntaje'], r['id']))

    return {
        'senales': senales,
        'es_premium': es_premium,
        'contenidos': [r for _, r in contenidos],
        'ejercicios': ejercicios,
    }
