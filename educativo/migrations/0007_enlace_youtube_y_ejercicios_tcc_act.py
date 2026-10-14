"""
1) Cambia el enlace de Spotify del contenido c3 (el episodio abría pero no
   reproducía) por un video de YouTube. Solo lo cambia si c3 todavía tiene el
   enlace original de Spotify, para no pisar uno cargado desde el admin.
2) Agrega dos ejercicios interactivos que tienen pantalla propia en el
   frontend:
   - e7: manejo de la catastrofización (TCC)
   - e8: valores personales (ACT)
"""
from django.db import migrations

SPOTIFY_ANTERIOR = 'https://open.spotify.com/episode/0cso6Ujkf9PPzZ69UxqVrr'
YOUTUBE_NUEVO = 'https://www.youtube.com/watch?v=zdH4U2PFBjg'

EJERCICIOS = [
    {
        'id': 'e7',
        'nombre': 'Manejo de la catastrofización',
        'tipo': 'tcc',
        'descripcion': 'Pon en perspectiva el "peor escenario" cuando el dolor te asusta.',
        'instrucciones': 'Describe el miedo, imagina el peor, el mejor y el más probable '
                         'escenario, y arma un plan para afrontarlo.',
        'minutos_estimados': 8,
    },
    {
        'id': 'e8',
        'nombre': 'Mis valores personales',
        'tipo': 'actMindfulness',
        'descripcion': 'Reconoce qué es importante para ti y da un paso pequeño hacia ello, '
                       'aunque haya dolor.',
        'instrucciones': 'Elige hasta tres valores, califica su importancia y define una '
                         'acción pequeña para esta semana.',
        'minutos_estimados': 7,
    },
]


def aplicar(apps, schema_editor):
    Contenido = apps.get_model('educativo', 'ContenidoEducativo')
    Ejercicio = apps.get_model('educativo', 'EjercicioPsicoeducativo')
    Contenido.objects.filter(id='c3', url_recurso=SPOTIFY_ANTERIOR).update(
        url_recurso=YOUTUBE_NUEVO,
        tipo='video',
        titulo='Endometriosis: más allá del dolor físico',
        resumen='Cómo la endometriosis también afecta el ánimo y qué ayuda a sobrellevarlo.',
    )
    for datos in EJERCICIOS:
        datos = dict(datos)
        Ejercicio.objects.update_or_create(id=datos.pop('id'), defaults=datos)


def revertir(apps, schema_editor):
    Ejercicio = apps.get_model('educativo', 'EjercicioPsicoeducativo')
    Ejercicio.objects.filter(id__in=[e['id'] for e in EJERCICIOS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('educativo', '0006_enlaces_recursos'),
    ]

    operations = [
        migrations.RunPython(aplicar, revertir),
    ]
