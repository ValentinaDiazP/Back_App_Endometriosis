"""
Contenido del gestor compartido por git.

Cada integrante del equipo tiene su propia base de datos local, así que lo
que se edita en el admin solo cambia en ese computador. Para compartirlo:

    python manage.py exportar_contenido_educativo   # guarda el archivo
    (git add / commit / push del archivo y de media/educativo/)
    python manage.py importar_contenido_educativo   # las demás lo cargan

El archivo (educativo/contenido/contenido_educativo.json) solo tiene el
catálogo: categorías, contenidos, ejercicios con sus pasos e indicaciones,
rutas, reglas de puntos, niveles e insignias. Nunca datos de usuarias.

Cada registro se identifica por su clave estable (el código de texto, la
clave de la regla, los puntos mínimos del nivel o la ruta de la insignia),
no por el id autonumérico, que cambia entre bases de datos.
"""
import datetime
import json
from pathlib import Path

from django.db import transaction

from .models import (
    CategoriaContenido,
    ContenidoEducativo,
    EjercicioPsicoeducativo,
    IndicacionPractica,
    InsigniaRuta,
    NivelAprendizaje,
    PasoModuloGuiado,
    ReglaAprendizaje,
    RutaAprendizaje,
    RutaAprendizajeContenido,
)

ARCHIVO = Path(__file__).resolve().parent / 'contenido' / 'contenido_educativo.json'
VERSION = 1


def _campos(obj, excluir=()):
    """Campos simples del objeto, listos para JSON (FK como su id)."""
    datos = {}
    for campo in obj._meta.concrete_fields:
        if campo.primary_key and campo.auto_created:
            continue
        if campo.attname in excluir:
            continue
        valor = getattr(obj, campo.attname)
        if isinstance(valor, (datetime.date, datetime.datetime)):
            valor = valor.isoformat()
        elif hasattr(valor, 'name') and hasattr(valor, 'storage'):  # ImageField
            valor = valor.name or ''
        datos[campo.attname] = valor
    return datos


def exportar():
    """Devuelve el catálogo como un dict listo para guardar en JSON."""
    return {
        'version': VERSION,
        'categorias': [_campos(c) for c in CategoriaContenido.objects.order_by('id')],
        'contenidos': [_campos(c) for c in ContenidoEducativo.objects.order_by('id')],
        'ejercicios': [
            {
                **_campos(e),
                'pasos': [
                    _campos(p, excluir=('ejercicio_id',))
                    for p in e.pasos_modulo.order_by('orden', 'id')
                ],
                'indicaciones': [
                    _campos(i, excluir=('ejercicio_id',))
                    for i in e.indicaciones.order_by('orden', 'id')
                ],
            }
            for e in EjercicioPsicoeducativo.objects.order_by('id')
        ],
        'rutas': [
            {
                **_campos(r),
                'contenidos': [p.contenido_id for p in r.pasos.order_by('orden')],
            }
            for r in RutaAprendizaje.objects.order_by('id')
        ],
        'reglas': [_campos(r) for r in ReglaAprendizaje.objects.order_by('clave')],
        'niveles': [_campos(n) for n in NivelAprendizaje.objects.order_by('puntos_minimos')],
        'insignias': [_campos(i) for i in InsigniaRuta.objects.order_by('ruta_id')],
    }


def guardar(ruta=ARCHIVO):
    datos = exportar()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return datos


@transaction.atomic
def importar(datos):
    """
    Crea o actualiza el catálogo con `datos`. Los pasos, indicaciones y el
    orden de cada ruta incluidos en el archivo reemplazan a los actuales. No
    borra contenidos ni ejercicios que no estén en el archivo (podrían tener
    progreso de usuarias asociado). Devuelve un resumen con lo cargado.
    """
    if datos.get('version') != VERSION:
        raise ValueError(f"Versión de archivo no soportada: {datos.get('version')}")

    for c in datos['categorias']:
        CategoriaContenido.objects.update_or_create(id=c['id'], defaults=c)
    for c in datos['contenidos']:
        ContenidoEducativo.objects.update_or_create(id=c['id'], defaults=c)

    for e in datos['ejercicios']:
        pasos, indicaciones = e['pasos'], e['indicaciones']
        campos = {k: v for k, v in e.items() if k not in ('pasos', 'indicaciones')}
        ejercicio, _ = EjercicioPsicoeducativo.objects.update_or_create(id=e['id'], defaults=campos)
        ejercicio.pasos_modulo.all().delete()
        PasoModuloGuiado.objects.bulk_create(PasoModuloGuiado(ejercicio=ejercicio, **p) for p in pasos)
        ejercicio.indicaciones.all().delete()
        IndicacionPractica.objects.bulk_create(
            IndicacionPractica(ejercicio=ejercicio, **i) for i in indicaciones
        )

    for r in datos['rutas']:
        orden_contenidos = r['contenidos']
        campos = {k: v for k, v in r.items() if k != 'contenidos'}
        ruta, _ = RutaAprendizaje.objects.update_or_create(id=r['id'], defaults=campos)
        ruta.pasos.all().delete()
        RutaAprendizajeContenido.objects.bulk_create(
            RutaAprendizajeContenido(ruta=ruta, contenido_id=c, orden=n)
            for n, c in enumerate(orden_contenidos, start=1)
        )

    for r in datos['reglas']:
        ReglaAprendizaje.objects.update_or_create(clave=r['clave'], defaults=r)
    for n in datos['niveles']:
        NivelAprendizaje.objects.update_or_create(puntos_minimos=n['puntos_minimos'], defaults=n)
    for i in datos['insignias']:
        InsigniaRuta.objects.update_or_create(ruta_id=i['ruta_id'], defaults=i)

    return {
        clave: len(datos[clave])
        for clave in ('categorias', 'contenidos', 'ejercicios', 'rutas', 'reglas', 'niveles', 'insignias')
    }


def cargar(ruta=ARCHIVO):
    return importar(json.loads(Path(ruta).read_text(encoding='utf-8')))
