from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from bienestar.models import Publicacion, Comentario, MeGusta, MeGustaComentario

class Command(BaseCommand):
    help = 'Pobla la base de datos con publicaciones, usuarias, comentarios y likes de comunidad de forma idempotente.'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando poblamiento de comunidad...')

        # 1. Crear usuarias con nombres naturales
        usuarias_data = [
            ('camila_r', 'Camila R.', 'camila@example.com'),
            ('laura_gomez', 'Laura Gómez', 'laura@example.com'),
            ('sofia_m', 'Sofía M.', 'sofia@example.com'),
            ('valentina_torres', 'Valentina Torres', 'valentina@example.com'),
            ('daniela_p', 'Daniela P.', 'daniela@example.com'),
            ('paula_andrea', 'Paula Andrea', 'paula@example.com'),
        ]

        users = {}
        for username, fullname, email in usuarias_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': email, 'first_name': fullname}
            )
            if created:
                user.set_password('123456')
                user.save()
            users[username] = user

        # 2. Definir las 15 publicaciones (5 por categoría)
        posts_data = [
            # ----------------------------------------------------
            # CATEGORÍA: DIAGNOSTICO_TRATAMIENTO (5 posts)
            # ----------------------------------------------------
            {
                'categoria': 'DIAGNOSTICO_TRATAMIENTO',
                'usuario': 'camila_r',
                'es_anonimo': False,
                'contenido': 'Hola chicas, por fin después de 4 años con dolores horribles me mandaron laparoscopia diagnóstica. ¿Alguna de ustedes se la ha hecho? ¿Cómo fue el postoperatorio los primeros días en casa?',
                'likes': ['laura_gomez', 'sofia_m', 'valentina_torres'],
                'comentarios': [
                    ('laura_gomez', 'Hola Camila! No te asustes, los primeros 3 días tira un poco por el gas que te ponen en la barriga, camina despacito por la casa y vas a ver que el alivio de tener diagnóstico vale totalmente la pena. ¡Mucho ánimo!', ['camila_r', 'sofia_m']),
                    ('sofia_m', 'A mí me fue súper bien con una almohadilla térmica en los hombros por el gas. Descansa mucho.', ['camila_r']),
                ]
            },
            {
                'categoria': 'DIAGNOSTICO_TRATAMIENTO',
                'usuario': 'laura_gomez',
                'es_anonimo': False,
                'contenido': 'Mi ginecólogo me recetó dienogest (progestina sola) para detener las reglas y controlar los focos. Al principio tuve un poco de manchado intermenstrual, ¿a alguna le pasó lo mismo al inicio?',
                'likes': ['camila_r', 'daniela_p'],
                'comentarios': [
                    ('daniela_p', '¡Sí, totalmente! Los primeros dos meses manchaba super poquito pero me asusté. El médico me dijo que era normal mientras el cuerpo se adaptaba. ¡Ten paciencia!', ['laura_gomez', 'paula_andrea']),
                    ('paula_andrea', 'A mí me cambió la vida, ya no tengo cólicos incapacitantes. Sigue con él.', ['laura_gomez']),
                ]
            },
            {
                'categoria': 'DIAGNOSTICO_TRATAMIENTO',
                'usuario': 'sofia_m',
                'es_anonimo': True,
                'contenido': 'Consejo de oro: cuando vayan a cita con el especialista, lleven un diario de síntomas de los últimos 2 meses impreso. A mí me sirvió para que el doctor me creyera de verdad y no lo minimizara.',
                'likes': ['camila_r', 'laura_gomez', 'valentina_torres', 'daniela_p'],
                'comentarios': [
                    ('valentina_torres', 'Qué gran consejo. Muchas veces una se bloquea en la consulta y se le olvida la mitad de las cosas que le duelen. Lo voy a hacer.', ['sofia_m', 'camila_r']),
                    ('camila_r', 'Totalmente de acuerdo, llevar datos objetivos le cierra la boca a cualquier médico incrédulo.', ['sofia_m']),
                ]
            },
            {
                'categoria': 'DIAGNOSTICO_TRATAMIENTO',
                'usuario': 'valentina_torres',
                'es_anonimo': False,
                'contenido': '¿Cuánto tiempo se demoraron en darles un diagnóstico certero? Siento que pase por 5 ginecólogos antes de que alguien me hablara de endometriosis profunda.',
                'likes': ['daniela_p', 'paula_andrea'],
                'comentarios': [
                    ('paula_andrea', 'Casi 7 años y 4 médicos diferentes que me decían que "era normal que la regla doliera". ¡Qué rabia da pensar en el tiempo perdido!', ['valentina_torres', 'camila_r']),
                ]
            },
            {
                'categoria': 'DIAGNOSTICO_TRATAMIENTO',
                'usuario': 'daniela_p',
                'es_anonimo': False,
                'contenido': 'Chicas, por favor nunca se automediquen con antiflamatorios fuertes sin supervisión ginecológica constante. A mí el estómago me pasó factura tras años tomando ibuprofeno diario.',
                'likes': ['camila_r', 'laura_gomez', 'sofia_m'],
                'comentarios': [
                    ('laura_gomez', 'Muy cierto Daniela. A mí me dio gastritis aguda por lo mismo. Ahora puro manejo integral.', ['daniela_p']),
                ]
            },

            # ----------------------------------------------------
            # CATEGORÍA: ESTILO_VIDA (5 posts)
            # ----------------------------------------------------
            {
                'categoria': 'ESTILO_VIDA',
                'usuario': 'paula_andrea',
                'es_anonimo': False,
                'contenido': 'Les comparto mi infusión favorita para los días de brote inflamatorio: jengibre rallado, cúrcuma, un toque de pimienta negra y limón. Me ayuda muchísimo con la hinchazón abdominal.',
                'likes': ['camila_r', 'laura_gomez', 'sofia_m', 'daniela_p', 'valentina_torres'],
                'comentarios': [
                    ('camila_r', '¡Qué delicia! La voy a preparar hoy mismo que ando con la inflamación a tope. Gracias por compartir.', ['paula_andrea', 'laura_gomez']),
                    ('sofia_m', 'Yo le echo un poquito de miel orgánica y queda perfecta.', ['paula_andrea']),
                ]
            },
            {
                'categoria': 'ESTILO_VIDA',
                'usuario': 'camila_r',
                'es_anonimo': False,
                'contenido': '¿Cómo manejan la jornada laboral cuando están con fatiga crónica y dolor pélvico? Yo compré un cojín térmico USB para la oficina y ha sido mi salvación.',
                'likes': ['laura_gomez', 'valentina_torres'],
                'comentarios': [
                    ('valentina_torres', '¡El cojín térmico USB es lo mejor del mundo! Yo lo tengo en mi silla de la oficina y nadie nota nada.', ['camila_r', 'daniela_p']),
                ]
            },
            {
                'categoria': 'ESTILO_VIDA',
                'usuario': 'laura_gomez',
                'es_anonimo': True,
                'contenido': 'Empecé yoga restaurativo enfocado en suelo pélvico hace un mes y he notado que la tensión muscular en la pelvis ha bajado un montón. ¿Alguna más practica yoga?',
                'likes': ['sofia_m', 'paula_andrea'],
                'comentarios': [
                    ('sofia_m', 'Sí! Con una profe especialista en suelo pélvico. Cambia totalmente la perspectiva de cómo mover el cuerpo sin lastimarnos.', ['laura_gomez', 'paula_andrea']),
                ]
            },
            {
                'categoria': 'ESTILO_VIDA',
                'usuario': 'sofia_m',
                'es_anonimo': False,
                'contenido': 'Reducir el azúcar refinada y los ultraprocesados un 80% me ayudó a disminuir los cólicos explosivos premenstruales. Al principio cuesta dejar el dulce, pero el cuerpo lo agradece.',
                'likes': ['camila_r', 'daniela_p', 'paula_andrea'],
                'comentarios': [
                    ('daniela_p', 'Me cuesta tanto el azúcar... pero tienes toda la razón. Intentaré dar el paso poco a poco.', ['sofia_m']),
                ]
            },
            {
                'categoria': 'ESTILO_VIDA',
                'usuario': 'valentina_torres',
                'es_anonimo': False,
                'contenido': 'Dormir 8 horas ya no es un lujo, es una necesidad médica para nosotras. Si no descanso bien, al día siguiente el dolor es el doble. ¿Les pasa igual?',
                'likes': ['camila_r', 'laura_gomez'],
                'comentarios': [
                    ('laura_gomez', 'Exacto! El sistema nervioso con endometriosis está hiperventilado, si no dormimos bien la inflamación se disparata.', ['valentina_torres']),
                ]
            },

            # ----------------------------------------------------
            # CATEGORÍA: HISTORIAS_APOYO (5 posts)
            # ----------------------------------------------------
            {
                'categoria': 'HISTORIAS_APOYO',
                'usuario': 'daniela_p',
                'es_anonimo': True,
                'contenido': 'Hoy tuve un día terrible en el trabajo. Nadie entendía por qué necesitaba ir al baño cada 20 minutos ni por qué mi cara era un poema del dolor. A veces me siento muy sola en esto.',
                'likes': ['camila_r', 'laura_gomez', 'sofia_m', 'valentina_torres', 'paula_andrea'],
                'comentarios': [
                    ('camila_r', 'Te abrazo fuerte desde la distancia, hermosa. No estás sola, aquí todas entendemos exactamente ese dolor invisible que la gente ignora.', ['daniela_p', 'laura_gomez', 'sofia_m']),
                    ('paula_andrea', 'Ánimo amiga, respira hondo. Tu salud está primero que cualquier empleo.', ['daniela_p']),
                ]
            },
            {
                'categoria': 'HISTORIAS_APOYO',
                'usuario': 'paula_andrea',
                'es_anonimo': False,
                'contenido': '¡Hoy celebré mi primer día sin dolor en semanas! Pude salir a caminar al parque con mi perrita sin llevar la bolsa de agua caliente colgada. Hay luz al final del túnel.',
                'likes': ['camila_r', 'sofia_m', 'valentina_torres'],
                'comentarios': [
                    ('camila_r', '¡Qué alegría tan grande! Disfruta cada segundo de ese alivio, te lo mereces muchísimo.', ['paula_andrea']),
                ]
            },
            {
                'categoria': 'HISTORIAS_APOYO',
                'usuario': 'camila_r',
                'es_anonimo': True,
                'contenido': 'Tenía terror de contarle a mi pareja sobre el diagnóstico y cómo esto afecta nuestra intimidad. Para mi sorpresa, fue súper comprensivo y me abrazó. No tengan miedo de abrir su corazón.',
                'likes': ['laura_gomez', 'daniela_p', 'paula_andrea'],
                'comentarios': [
                    ('laura_gomez', 'Qué hermoso leer esto. El amor verdadero y consciente sí existe y nos acompaña en el proceso.', ['camila_r']),
                ]
            },
            {
                'categoria': 'HISTORIAS_APOYO',
                'usuario': 'laura_gomez',
                'es_anonimo': False,
                'contenido': 'A veces el duelo por la salud que teníamos antes y ya no tenemos es durísimo. Permitirse llorar y estar triste también es parte de sanar y avanzar.',
                'likes': ['camila_r', 'sofia_m', 'valentina_torres', 'daniela_p'],
                'comentarios': [
                    ('sofia_m', 'Qué sabias palabras, Laura. Validar nuestra tristeza es el primer paso para no cargarlas solas.', ['laura_gomez', 'camila_r']),
                ]
            },
            {
                'categoria': 'HISTORIAS_APOYO',
                'usuario': 'sofia_m',
                'es_anonimo': False,
                'contenido': 'Gracias a todas las que escriben aquí diario. Encontrar esta comunidad en la app de Bienestar me devolvió la paz mental que había perdido en las salas de espera.',
                'likes': ['camila_r', 'laura_gomez', 'valentina_torres', 'paula_andrea'],
                'comentarios': [
                    ('valentina_torres', '¡Totalmente! Florecer juntas hace que el camino sea más liviano y hermoso. 💜', ['sofia_m', 'paula_andrea']),
                ]
            },
        ]

        # 3. Crear las publicaciones de forma idempotente y asignar fechas escalonadas
        base_time = timezone.now()

        for idx, p_data in enumerate(posts_data):
            user = users[p_data['usuario']]
            
            # Verificar si ya existe una publicación similar con el mismo contenido
            pub, created = Publicacion.objects.get_or_create(
                contenido=p_data['contenido'],
                defaults={
                    'usuario': user,
                    'estado': 'APROBADO',
                    'categoria': p_data['categoria'],
                    'es_anonimo': p_data['es_anonimo'],
                }
            )

            # Ajustar fecha de creación escalonada (desde hace 10 días hasta hace unas horas)
            dias_atras = 10 - (idx * 0.6)
            nueva_fecha = base_time - timedelta(days=dias_atras)
            Publicacion.objects.filter(id=pub.id).update(fecha_creacion=nueva_fecha)

            # Asignar likes a la publicación
            for liker_username in p_data['likes']:
                liker = users[liker_username]
                MeGusta.objects.get_or_create(publicacion=pub, usuario=liker)

            # Asignar comentarios y likes a los comentarios
            for comment_idx, (comment_user_name, comment_text, comment_likes_users) in enumerate(p_data['comentarios']):
                comment_user = users[comment_user_name]
                comentario, c_created = Comentario.objects.get_or_create(
                    publicacion=pub,
                    usuario=comment_user,
                    texto=comment_text,
                )
                # Escalonar fecha del comentario también
                Comentario.objects.filter(id=comentario.id).update(
                    fecha_creacion=nueva_fecha + timedelta(hours=comment_idx + 1)
                )

                # Asignar likes al comentario (esto alimenta el "Top comentarios" y la insignia de Más apoyado)
                for c_liker_name in comment_likes_users:
                    c_liker = users[c_liker_name]
                    MeGustaComentario.objects.get_or_create(comentario=comentario, usuario=c_liker)

            self.stdout.write(f"[{idx+1}/15] Publicación procesada (Categoría: {p_data['categoria']})")

        self.stdout.write(self.style.SUCCESS('¡Comunidad poblada exitosamente con 15 publicaciones, comentarios y top likes!'))
