"""
Carga los enlaces externos (videos, podcasts y meditaciones guiadas) de
algunos contenidos y ejercicios. Fuentes elegidas por ser médicas,
hospitalarias o universitarias:

- Mayo Clinic (canal oficial de YouTube, en español).
- Brainman / Hunter Integrated Pain Service (hospital público de Australia).
- Podcast con el Dr. Fernando Akerman, ginecólogo (Spotify).
- UCLA Mindful (meditaciones guiadas gratuitas en español).

Solo llena el enlace si está vacío, para no pisar uno cargado desde el admin.
"""
from django.db import migrations

CONTENIDOS = {
    # ¿Qué es la endometriosis?
    'c1': 'https://www.youtube.com/watch?v=drez6fzeVzg',
    # Entendiendo el dolor crónico
    'c2': 'https://www.youtube.com/watch?v=5KrUL8tOaQs',
    # Rutina de autocuidado para días difíciles
    'c3': 'https://open.spotify.com/episode/0cso6Ujkf9PPzZ69UxqVrr',
}

EJERCICIOS = {
    # Aceptar el dolor sin pelear contra él (ACT)
    'e3': 'https://www.uclahealth.org/marc/mpeg/Spanish-workingwithdifficulties.mp3',
    # Mindfulness para el dolor pélvico
    'e4': 'https://www.uclahealth.org/marc/mpeg/breathsoundbody-espanol.mp3',
}


def cargar_enlaces(apps, schema_editor):
    Contenido = apps.get_model('educativo', 'ContenidoEducativo')
    Ejercicio = apps.get_model('educativo', 'EjercicioPsicoeducativo')
    for id_, url in CONTENIDOS.items():
        Contenido.objects.filter(id=id_, url_recurso='').update(url_recurso=url)
    for id_, url in EJERCICIOS.items():
        Ejercicio.objects.filter(id=id_, url_recurso='').update(url_recurso=url)


def quitar_enlaces(apps, schema_editor):
    Contenido = apps.get_model('educativo', 'ContenidoEducativo')
    Ejercicio = apps.get_model('educativo', 'EjercicioPsicoeducativo')
    for id_, url in CONTENIDOS.items():
        Contenido.objects.filter(id=id_, url_recurso=url).update(url_recurso='')
    for id_, url in EJERCICIOS.items():
        Ejercicio.objects.filter(id=id_, url_recurso=url).update(url_recurso='')


class Migration(migrations.Migration):

    dependencies = [
        ('educativo', '0005_url_recurso'),
    ]

    operations = [
        migrations.RunPython(cargar_enlaces, quitar_enlaces),
    ]
