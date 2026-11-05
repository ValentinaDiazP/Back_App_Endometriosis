"""
Carga en la base de datos el contenido que antes vivía en el código del
frontend (Flutter): los pasos de los módulos guiados de psicoeducación y las
indicaciones de las prácticas guiadas de ACT/Mindfulness. Desde ahora se
editan desde el admin de Django.

Solo carga el contenido de un ejercicio si todavía no tiene pasos ni
indicaciones, para no pisar lo que se haya editado en el admin.
"""
from django.db import migrations

# id de ejercicio -> lista de pasos (titulo, parrafos, punto_clave)
PASOS = {
    "e1": [
        {
            "titulo": "Tu dolor es real",
            "parrafos": [
                "Cuando vives con endometriosis, el dolor no es \"exageración\" ni algo que esté solo en tu cabeza. Es una experiencia real, con causas físicas y también con otros factores que influyen.",
                "En este módulo vas a entender, paso a paso, qué puede estar pasando en tu cuerpo cuando duele. Entenderlo no hace que el dolor desaparezca, pero puede darte más calma y más control."
            ],
            "punto_clave": "Tu dolor es real y merece ser tomado en serio."
        },
        {
            "titulo": "Dolor agudo y dolor crónico",
            "parrafos": [
                "El dolor agudo es una alarma: aparece ante una lesión y se va cuando el cuerpo se recupera.",
                "El dolor crónico es el que dura meses. Con el tiempo, la alarma puede seguir sonando aunque no haya un daño nuevo, y por eso a veces cuesta entenderlo."
            ],
            "punto_clave": "Un dolor que dura mucho tiempo funciona distinto a un dolor reciente."
        },
        {
            "titulo": "Un sistema nervioso más sensible",
            "parrafos": [
                "Cuando el dolor se repite, el sistema nervioso puede volverse más sensible y reaccionar con más intensidad a estímulos que antes dolían menos. A esto se le llama sensibilización.",
                "No es una falla tuya: es una forma en que el cuerpo se adapta al dolor sostenido."
            ],
            "punto_clave": "La sensibilidad aumentada es una adaptación del cuerpo, no una debilidad."
        },
        {
            "titulo": "Lo que puede amplificar el dolor",
            "parrafos": [
                "El estrés, dormir poco, la preocupación constante y el miedo a que llegue el dolor pueden hacer que se sienta con más intensidad.",
                "Esto no significa que \"te lo causes tú\". Significa que el cuerpo y las emociones están conectados, y que hay cosas que sí puedes influir."
            ],
            "punto_clave": "Estrés, sueño y emociones influyen en cómo se siente el dolor."
        },
        {
            "titulo": "Lo que sí puedes hacer",
            "parrafos": [
                "Registrar tus síntomas, cuidar tus descansos, moverte con suavidad cuando puedas y practicar ejercicios de calma son pequeñas acciones que suman.",
                "En los siguientes ejercicios de la app aprenderás herramientas concretas. Y si el dolor te limita mucho, habla con tu profesional de salud."
            ],
            "punto_clave": "Pequeñas acciones constantes ayudan, y no tienes que hacerlo sola."
        }
    ],
    "e5": [
        {
            "titulo": "El círculo del dolor y el estrés",
            "parrafos": [
                "Cuando duele, es normal sentir tensión y preocupación. Esa tensión puede aumentar la sensación de dolor, y más dolor genera más estrés. Así se forma un círculo."
            ],
            "punto_clave": "Dolor y estrés pueden alimentarse entre sí."
        },
        {
            "titulo": "Cómo se siente en el ánimo",
            "parrafos": [
                "Vivir con dolor frecuente cansa. Es habitual sentir tristeza, irritabilidad o desánimo en algunos días.",
                "Estas emociones no son un fallo personal: son una respuesta comprensible a una situación difícil."
            ],
            "punto_clave": "Sentirte así es comprensible, no es un defecto tuyo."
        },
        {
            "titulo": "Dónde puedes cortar el círculo",
            "parrafos": [
                "No se trata de eliminar el estrés por completo, sino de bajar un poco la intensidad: respirar con calma, hacer pausas, hablar con alguien de confianza.",
                "Cada pausa pequeña le da al cuerpo una señal de seguridad."
            ],
            "punto_clave": "Pausas pequeñas también cuentan."
        },
        {
            "titulo": "Cuándo pedir ayuda",
            "parrafos": [
                "Si notas que la tristeza o la ansiedad se vuelven constantes o te impiden hacer tu vida diaria, conviene hablarlo con un profesional de salud o de salud mental.",
                "Pedir ayuda es una forma de cuidarte."
            ],
            "punto_clave": "Pedir ayuda es parte del autocuidado."
        }
    ],
    "e6": [
        {
            "titulo": "Por qué importa el ritmo",
            "parrafos": [
                "En los días buenos es tentador hacer todo de una vez. Pero pasarse puede traer un día de más dolor después. Y en los días malos, no hacer nada puede dejarte más rígida."
            ],
            "punto_clave": "Ni todo de golpe ni nada: busca un punto medio."
        },
        {
            "titulo": "Dosificar tu energía",
            "parrafos": [
                "Dosificar significa dividir las actividades en partes pequeñas y alternar con descansos antes de sentirte agotada, no después."
            ],
            "punto_clave": "Descansar antes de agotarte ayuda a sostener el día."
        },
        {
            "titulo": "Escucha tu cuerpo, sin juzgarte",
            "parrafos": [
                "Algunos días harás más y otros menos. Cambiar el plan no es fracasar: es adaptarte a cómo está tu cuerpo hoy."
            ],
            "punto_clave": "Adaptar el plan no es fracasar."
        },
        {
            "titulo": "Tu primer paso",
            "parrafos": [
                "Elige una actividad de tu día y piensa cómo dividirla en dos o tres partes con una pausa en medio.",
                "Puedes usar el seguimiento de la app para notar qué días te cuestan más y ajustar tu ritmo."
            ],
            "punto_clave": "Empieza con una sola actividad y una pausa."
        }
    ]
}

# id de ejercicio -> lista de indicaciones, en orden
INDICACIONES = {
    "e3": [
        "Busca una postura cómoda. Si quieres, cierra los ojos.",
        "Respira con calma. No tienes que hacerlo de ninguna forma especial.",
        "Nota dónde sientes el dolor ahora mismo. No intentes cambiarlo: solo obsérvalo.",
        "Ponle nombre: \"estoy notando una sensación de…\" (presión, calor, punzada).",
        "Imagina que le haces espacio, como si respiraras alrededor de esa sensación.",
        "Si aparecen pensamientos como \"no lo soporto\", déjalos pasar como nubes.",
        "Recuerda algo que te importa hoy, aunque el dolor esté presente.",
        "Vuelve a tu respiración. Cuando estés lista, abre los ojos despacio."
    ],
    "e4": [
        "Siéntate o recuéstate en un lugar tranquilo. Apoya una mano en tu abdomen.",
        "Inhala por la nariz y siente cómo sube tu mano. Exhala despacio por la boca.",
        "Lleva la atención a tus pies y tus piernas. Nota si hay tensión y suéltala.",
        "Sube la atención a tus caderas y a la parte baja de la espalda.",
        "Ahora, a tu zona pélvica. Obsérvala con amabilidad, sin juzgar lo que sientes.",
        "Con cada exhalación, imagina que esa zona se ablanda un poco.",
        "Si tu mente se distrae, está bien. Vuelve con suavidad a la respiración.",
        "Nota tu cuerpo completo. Cuando quieras, mueve los dedos y abre los ojos."
    ]
}


def cargar(apps, schema_editor):
    Ejercicio = apps.get_model('educativo', 'EjercicioPsicoeducativo')
    Paso = apps.get_model('educativo', 'PasoModuloGuiado')
    Indicacion = apps.get_model('educativo', 'IndicacionPractica')

    for id_, pasos in PASOS.items():
        if not Ejercicio.objects.filter(id=id_).exists() or Paso.objects.filter(ejercicio_id=id_).exists():
            continue
        for orden, paso in enumerate(pasos, start=1):
            Paso.objects.create(
                ejercicio_id=id_,
                orden=orden,
                titulo=paso['titulo'],
                texto='\n\n'.join(paso['parrafos']),
                punto_clave=paso['punto_clave'],
            )

    for id_, textos in INDICACIONES.items():
        if not Ejercicio.objects.filter(id=id_).exists() or Indicacion.objects.filter(ejercicio_id=id_).exists():
            continue
        for orden, texto in enumerate(textos, start=1):
            Indicacion.objects.create(ejercicio_id=id_, orden=orden, texto=texto)


def quitar(apps, schema_editor):
    apps.get_model('educativo', 'PasoModuloGuiado').objects.filter(ejercicio_id__in=list(PASOS)).delete()
    apps.get_model('educativo', 'IndicacionPractica').objects.filter(ejercicio_id__in=list(INDICACIONES)).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('educativo', '0014_gestor_contenidos'),
    ]

    operations = [
        migrations.RunPython(cargar, quitar),
    ]
