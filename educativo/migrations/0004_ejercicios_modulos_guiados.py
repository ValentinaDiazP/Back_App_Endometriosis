"""
Agrega los ejercicios de psicoeducación e5 y e6, que tienen módulo guiado
en el frontend (modulos_psicoeducativos_mock.dart). Copiados de
mock_educativo_data.dart del frontend.
"""
from django.db import migrations

EJERCICIOS = [
    {
        'id': 'e5',
        'nombre': 'Dolor, estrés y ánimo: cómo se conectan',
        'tipo': 'psicoeducacion',
        'descripcion': 'Módulo guiado sobre la relación entre dolor y emociones.',
        'instrucciones': 'Avanza paso a paso y lee con calma.',
        'minutos_estimados': 6,
    },
    {
        'id': 'e6',
        'nombre': 'Ritmo y descanso: dosifica tu energía',
        'tipo': 'psicoeducacion',
        'descripcion': 'Módulo guiado para organizar tus días con dolor.',
        'instrucciones': 'Avanza paso a paso y lee con calma.',
        'minutos_estimados': 5,
    },
]


def agregar_ejercicios(apps, schema_editor):
    Ejercicio = apps.get_model('educativo', 'EjercicioPsicoeducativo')
    for datos in EJERCICIOS:
        datos = dict(datos)
        Ejercicio.objects.update_or_create(id=datos.pop('id'), defaults=datos)


def quitar_ejercicios(apps, schema_editor):
    apps.get_model('educativo', 'EjercicioPsicoeducativo').objects.filter(
        id__in=[e['id'] for e in EJERCICIOS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('educativo', '0003_datos_usuaria'),
    ]

    operations = [
        migrations.RunPython(agregar_ejercicios, quitar_ejercicios),
    ]
