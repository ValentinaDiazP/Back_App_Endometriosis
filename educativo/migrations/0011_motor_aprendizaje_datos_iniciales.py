"""
Carga las reglas de puntos, los niveles y las insignias de las rutas
iniciales (r1 y r2). Todo se puede editar después desde el admin.
Solo crea lo que no existe, para no pisar cambios hechos en el admin.
"""
from django.db import migrations

REGLAS = [
    ('contenido_leido', 'Leíste un contenido', 10),
    ('ejercicio_completado', 'Completaste un ejercicio', 15),
    ('ruta_completada', 'Completaste una ruta de aprendizaje', 50),
    ('racha_aprendizaje_3', 'Racha de aprendizaje de 3 días', 10),
    ('racha_aprendizaje_7', 'Racha de aprendizaje de 7 días', 25),
    ('racha_aprendizaje_30', 'Racha de aprendizaje de 30 días', 100),
]

NIVELES = [
    ('Exploradora', 0, '🧭'),
    ('Aprendiz', 50, '📖'),
    ('Conocedora', 150, '💡'),
    ('Experta', 350, '🎓'),
    ('Guía', 600, '🌟'),
]

# (id de la ruta, nombre, descripción, emoji)
INSIGNIAS = [
    ('r1', 'Primeros pasos', 'Completaste la ruta de primeros pasos con la endometriosis.', '🌱'),
    ('r2', 'Mente y dolor', 'Completaste la ruta de manejo del dolor con enfoque TCC.', '🧠'),
]


def cargar(apps, schema_editor):
    Regla = apps.get_model('educativo', 'ReglaAprendizaje')
    Nivel = apps.get_model('educativo', 'NivelAprendizaje')
    Insignia = apps.get_model('educativo', 'InsigniaRuta')
    Ruta = apps.get_model('educativo', 'RutaAprendizaje')

    for clave, descripcion, puntos in REGLAS:
        Regla.objects.get_or_create(clave=clave, defaults={'descripcion': descripcion, 'puntos': puntos})
    for nombre, minimos, emoji in NIVELES:
        Nivel.objects.get_or_create(puntos_minimos=minimos, defaults={'nombre': nombre, 'emoji': emoji})
    for ruta_id, nombre, descripcion, emoji in INSIGNIAS:
        if Ruta.objects.filter(id=ruta_id).exists():
            Insignia.objects.get_or_create(
                ruta_id=ruta_id,
                defaults={'nombre': nombre, 'descripcion': descripcion, 'emoji': emoji},
            )


def quitar(apps, schema_editor):
    apps.get_model('educativo', 'ReglaAprendizaje').objects.filter(
        clave__in=[r[0] for r in REGLAS]
    ).delete()
    apps.get_model('educativo', 'NivelAprendizaje').objects.filter(
        puntos_minimos__in=[n[1] for n in NIVELES]
    ).delete()
    apps.get_model('educativo', 'InsigniaRuta').objects.filter(
        ruta_id__in=[i[0] for i in INSIGNIAS]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('educativo', '0010_motor_aprendizaje'),
    ]

    operations = [
        migrations.RunPython(cargar, quitar),
    ]
