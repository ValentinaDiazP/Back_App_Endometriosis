"""
Marca como premium los dos ejercicios interactivos más nuevos:
e7 (Manejo de la catastrofización, TCC) y e8 (Mis valores personales, ACT).
Los demás ejercicios siguen siendo gratuitos. Se puede cambiar desde el admin.
"""
from django.db import migrations

EJERCICIOS_PREMIUM = ['e7', 'e8']


def marcar(apps, schema_editor):
    apps.get_model('educativo', 'EjercicioPsicoeducativo').objects.filter(
        id__in=EJERCICIOS_PREMIUM
    ).update(es_premium=True)


def desmarcar(apps, schema_editor):
    apps.get_model('educativo', 'EjercicioPsicoeducativo').objects.filter(
        id__in=EJERCICIOS_PREMIUM
    ).update(es_premium=False)


class Migration(migrations.Migration):

    dependencies = [
        ('educativo', '0012_ejercicio_es_premium'),
    ]

    operations = [
        migrations.RunPython(marcar, desmarcar),
    ]
