from django.db import migrations


def actualizar_reglas_y_humanizar(apps, schema_editor):
    ReglaPuntos = apps.get_model('sintomas', 'ReglaPuntos')
    NivelGamificacion = apps.get_model('sintomas', 'NivelGamificacion')

    # 1. Agregar las reglas nuevas de citas y continuidad (si no existen)
    reglas_nuevas = [
        ('cita_medica', 'Agendaste un espacio de autocuidado con un especialista', 15),
        ('cita_completada', 'Completaste tu sesión de bienestar con el especialista', 25),
        ('vinculo_confianza', 'Vínculo de Confianza: Completaste 3 encuentros con el mismo especialista para cuidar tu bienestar', 50),
    ]
    for clave, descripcion, puntos in reglas_nuevas:
        ReglaPuntos.objects.get_or_create(
            clave=clave,
            defaults={'descripcion': descripcion, 'puntos': puntos, 'activa': True}
        )

    # 2. Humanizar los textos de las reglas existentes respetando claves internas
    traducciones_humanas = {
        'registro_sintoma': 'Registraste cómo se siente tu cuerpo hoy, un acto valioso de escucha',
        'registro_ciclo': 'Registraste tu ciclo menstrual para honrar tusritmos naturales',
        'checkin_emocional': 'Hiciste tu check-in emocional diario para abrazar lo que sientes',
        'racha_7': '¡Racha de 7 días! Una semana entera cultivando tu bienestar con constancia',
        'racha_30': '¡Racha de 30 días! Un mes entero floreciendo y acompañando tu salud con amor',
        'racha_90': '¡Racha de 90 días! Tres meses de compromiso profundo con tu bienestar integral',
        'comunidad_post': 'Compartiste tu historia en la comunidad para abrazar y conectar con otras',
        'comunidad_comentario': 'Dejaste un mensaje de apoyo y empatía en la comunidad',
    }

    for clave, desc_humana in traducciones_humanas.items():
        regla = ReglaPuntos.objects.filter(clave=clave).first()
        if regla:
            regla.descripcion = desc_humana
            regla.save()

    # 3. Humanizar los nombres de los niveles de gamificación existentes
    niveles_humanos = {
        0: 'Semilla Consciente',
        50: 'Brote de Bienestar',
        150: 'Capullo en Flor',
        300: 'Jardín Vital',
        600: 'Bosque Radiante'
    }

    for puntos_min, nombre_humana in niveles_humanos.items():
        nivel = NivelGamificacion.objects.filter(puntos_minimos=puntos_min).first()
        if nivel:
            nivel.nombre = nombre_humana
            nivel.save()
        else:
            NivelGamificacion.objects.get_or_create(
                puntos_minimos=puntos_min,
                defaults={'nombre': nombre_humana}
            )


class Migration(migrations.Migration):

    dependencies = [
        ('sintomas', '0008_registroemocional_capacidad_dia_and_more'),
    ]

    operations = [
        migrations.RunPython(actualizar_reglas_y_humanizar, migrations.RunPython.noop),
    ]
