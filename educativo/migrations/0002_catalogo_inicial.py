"""
Carga el catálogo inicial del módulo Educativo, copiado de
`mock_educativo_data.dart` del frontend, para que la app tenga contenido
apenas se corra `migrate`. Después, el contenido se administra desde el
admin de Django.
"""
import datetime

from django.db import migrations

CATEGORIAS = [
    ('cat_endometriosis', 'Endometriosis', 'Qué es, cómo se diagnostica y cómo evoluciona.'),
    ('cat_dolor', 'Dolor crónico', 'Entender el dolor persistente y cómo manejarlo.'),
    ('cat_autocuidado', 'Autocuidado', 'Hábitos, alimentación y bienestar emocional diario.'),
]

CONTENIDOS = [
    {
        'id': 'c1',
        'categoria_id': 'cat_endometriosis',
        'titulo': '¿Qué es la endometriosis?',
        'tipo': 'texto',
        'nivel': 'basico',
        'es_premium': False,
        'fecha_publicacion': datetime.date(2026, 1, 10),
        'resumen': 'Una introducción clara a qué le pasa a tu cuerpo.',
        'cuerpo': (
            'La endometriosis es una condición en la que tejido similar al '
            'endometrio crece fuera del útero... (contenido de ejemplo)'
        ),
        'minutos_estimados': 5,
    },
    {
        'id': 'c2',
        'categoria_id': 'cat_dolor',
        'titulo': 'Entendiendo el dolor crónico',
        'tipo': 'video',
        'nivel': 'basico',
        'es_premium': False,
        'fecha_publicacion': datetime.date(2026, 1, 12),
        'resumen': 'Por qué el dolor persiste incluso sin daño activo.',
        'cuerpo': 'Guion del video de ejemplo...',
        'minutos_estimados': 8,
    },
    {
        'id': 'c3',
        'categoria_id': 'cat_autocuidado',
        'titulo': 'Rutina de autocuidado para días difíciles',
        'tipo': 'audio',
        'nivel': 'intermedio',
        'es_premium': False,
        'fecha_publicacion': datetime.date(2026, 1, 15),
        'resumen': 'Pequeños hábitos para los días de más dolor.',
        'cuerpo': 'Guion del audio de ejemplo...',
        'minutos_estimados': 6,
    },
    {
        'id': 'c4',
        'categoria_id': 'cat_dolor',
        'titulo': 'Catastrofización del dolor: cómo identificarla',
        'tipo': 'texto',
        'nivel': 'avanzado',
        'es_premium': True,
        'fecha_publicacion': datetime.date(2026, 1, 20),
        'resumen': 'Contenido premium con enfoque TCC.',
        'cuerpo': 'Contenido de ejemplo premium...',
        'minutos_estimados': 10,
    },
]

EJERCICIOS = [
    {
        'id': 'e1',
        'nombre': '¿Qué le pasa a mi cuerpo cuando duele?',
        'tipo': 'psicoeducacion',
        'descripcion': 'Módulo guiado para entender el ciclo del dolor.',
        'instrucciones': 'Lee cada tarjeta y marca la casilla al terminar. Tómate tu tiempo.',
        'minutos_estimados': 7,
    },
    {
        'id': 'e2',
        'nombre': 'Reestructurando pensamientos catastróficos',
        'tipo': 'tcc',
        'descripcion': 'Identifica y transforma pensamientos como "esto nunca va a mejorar".',
        'instrucciones': 'Escribe un pensamiento difícil, luego una versión más balanceada.',
        'minutos_estimados': 10,
    },
    {
        'id': 'e3',
        'nombre': 'Aceptar el dolor sin pelear contra él',
        'tipo': 'actMindfulness',
        'descripcion': 'Ejercicio de aceptación basado en ACT.',
        'instrucciones': 'Sigue el audio guiado de 5 minutos.',
        'minutos_estimados': 5,
    },
    {
        'id': 'e4',
        'nombre': 'Mindfulness para el dolor pélvico',
        'tipo': 'actMindfulness',
        'descripcion': 'Práctica breve de atención plena orientada al dolor.',
        'instrucciones': 'Busca un lugar tranquilo y sigue las instrucciones.',
        'minutos_estimados': 8,
    },
]

# (id, nombre, descripcion, [ids de contenido en orden])
RUTAS = [
    ('r1', 'Primeros pasos con la endometriosis',
     'Ruta introductoria para usuarias recién diagnosticadas.', ['c1', 'c2', 'c3']),
    ('r2', 'Manejo del dolor con enfoque TCC',
     'Ruta intermedia centrada en pensamientos y dolor.', ['c2', 'c4']),
]


def cargar_catalogo(apps, schema_editor):
    Categoria = apps.get_model('educativo', 'CategoriaContenido')
    Contenido = apps.get_model('educativo', 'ContenidoEducativo')
    Ejercicio = apps.get_model('educativo', 'EjercicioPsicoeducativo')
    Ruta = apps.get_model('educativo', 'RutaAprendizaje')
    RutaContenido = apps.get_model('educativo', 'RutaAprendizajeContenido')

    for id_, nombre, descripcion in CATEGORIAS:
        Categoria.objects.update_or_create(id=id_, defaults={'nombre': nombre, 'descripcion': descripcion})
    for datos in CONTENIDOS:
        datos = dict(datos)
        Contenido.objects.update_or_create(id=datos.pop('id'), defaults=datos)
    for datos in EJERCICIOS:
        datos = dict(datos)
        Ejercicio.objects.update_or_create(id=datos.pop('id'), defaults=datos)
    for id_, nombre, descripcion, ids_contenido in RUTAS:
        ruta, _ = Ruta.objects.update_or_create(
            id=id_, defaults={'nombre': nombre, 'descripcion': descripcion}
        )
        RutaContenido.objects.filter(ruta=ruta).delete()
        for orden, id_contenido in enumerate(ids_contenido, start=1):
            RutaContenido.objects.create(ruta=ruta, contenido_id=id_contenido, orden=orden)


def borrar_catalogo(apps, schema_editor):
    apps.get_model('educativo', 'RutaAprendizaje').objects.filter(id__in=[r[0] for r in RUTAS]).delete()
    apps.get_model('educativo', 'EjercicioPsicoeducativo').objects.filter(id__in=[e['id'] for e in EJERCICIOS]).delete()
    apps.get_model('educativo', 'ContenidoEducativo').objects.filter(id__in=[c['id'] for c in CONTENIDOS]).delete()
    apps.get_model('educativo', 'CategoriaContenido').objects.filter(id__in=[c[0] for c in CATEGORIAS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('educativo', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(cargar_catalogo, borrar_catalogo),
    ]
