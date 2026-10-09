from django.db import migrations


def cargar_reglas_comunidad(apps, schema_editor):
    ReglaPuntos = apps.get_model('sintomas', 'ReglaPuntos')
    reglas = [
        ('comunidad_post', 'Publicación en comunidad', 10),
        ('comunidad_comentario', 'Comentario en comunidad', 5),
    ]
    for clave, descripcion, puntos in reglas:
        ReglaPuntos.objects.get_or_create(
            clave=clave,
            defaults={'descripcion': descripcion, 'puntos': puntos},
        )


class Migration(migrations.Migration):
    dependencies = [
        ('sintomas', '0005_registrociclo'),
    ]

    operations = [
        migrations.RunPython(cargar_reglas_comunidad, migrations.RunPython.noop),
    ]
