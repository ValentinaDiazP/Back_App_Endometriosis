from django.core.management.base import BaseCommand
from bienestar.models import Professional, DisponibilidadProfesional, Producto
from decimal import Decimal

class Command(BaseCommand):
    help = 'Pobla la base de datos con profesionales especializados en endometriosis, sus horarios de disponibilidad y productos variados de la Tienda de forma idempotente.'

    def handle(self, *args, **options):
        self.stdout.write('Iniciando poblamiento de profesionales y productos de bienestar...')

        # 1. Profesionales especializados en endometriosis (5 profesionales)
        profesionales_data = [
            {
                'name': 'Dra. Marcela Restrepo',
                'specialty': 'Ginecología y Cirugía de Endometriosis',
                'rate': '$180.000 COP',
                'availability': 'Lun, Mié, Vie (08:00 - 16:00)',
                'whatsapp': '573001234567',
                'horarios': [
                    ('Lunes', '08:00', '16:00'),
                    ('Miércoles', '08:00', '16:00'),
                    ('Viernes', '08:00', '16:00'),
                ]
            },
            {
                'name': 'Lic. Andrea Cifuentes',
                'specialty': 'Fisioterapia de Suelo Pélvico',
                'rate': '$140.000 COP',
                'availability': 'Mar, Jue, Sáb (09:00 - 17:00)',
                'whatsapp': '573112345678',
                'horarios': [
                    ('Martes', '09:00', '17:00'),
                    ('Jueves', '09:00', '17:00'),
                    ('Sábado', '09:00', '13:00'),
                ]
            },
            {
                'name': 'Dra. Claudia Morales',
                'specialty': 'Nutrición Antiinflamatoria y Hormonal',
                'rate': '$130.000 COP',
                'availability': 'Lun, Mar, Jue (10:00 - 18:00)',
                'whatsapp': '573203456789',
                'horarios': [
                    ('Lunes', '10:00', '18:00'),
                    ('Martes', '10:00', '18:00'),
                    ('Jueves', '10:00', '18:00'),
                ]
            },
            {
                'name': 'Psic. Juliana Echeverría',
                'specialty': 'Psicología del Dolor Crónico',
                'rate': '$120.000 COP',
                'availability': 'Mié, Jue, Vie (13:00 - 20:00)',
                'whatsapp': '573154567890',
                'horarios': [
                    ('Miércoles', '13:00', '20:00'),
                    ('Jueves', '13:00', '20:00'),
                    ('Viernes', '13:00', '20:00'),
                ]
            },
            {
                'name': 'Dr. Santiago Vargas',
                'specialty': 'Medicina Funcional y Manejo del Dolor',
                'rate': '$200.000 COP',
                'availability': 'Lun, Mié, Sáb (08:00 - 14:00)',
                'whatsapp': '573185678901',
                'horarios': [
                    ('Lunes', '08:00', '14:00'),
                    ('Miércoles', '08:00', '14:00'),
                    ('Sábado', '08:00', '14:00'),
                ]
            },
        ]

        for p_data in profesionales_data:
            horarios = p_data.pop('horarios')
            prof, created = Professional.objects.get_or_create(
                name=p_data['name'],
                defaults=p_data
            )
            if not created:
                # Actualizar datos si ya existe
                for key, val in p_data.items():
                    setattr(prof, key, val)
                prof.save()
                self.stdout.write(f"Profesional actualizado: {prof.name}")
            else:
                self.stdout.write(f"Profesional creado: {prof.name}")

            # Crear o asegurar disponibilidades
            for dia, h_inicio, h_fin in horarios:
                DisponibilidadProfesional.objects.get_or_create(
                    profesional=prof,
                    dia_semana=dia,
                    hora_inicio=h_inicio,
                    hora_fin=h_fin
                )

        # 2. Productos variados (8 productos cubriendo todas las categorías)
        productos_data = [
            {
                'nombre': 'Bolsa Térmica Terapéutica de Semillas',
                'descripcion': 'Almohadilla térmica con semillas naturales y lavanda, diseñada para calmar el dolor pélvico y lumbar asociado a la endometriosis.',
                'composicion': 'Semillas de trigo, flores de lavanda orgánica, funda de algodón 100% removible.',
                'precio': Decimal('48000.00'),
                'marca': 'Florecer',
                'categoria': 'ALIVIO_DOLOR',
                'imagen_url': 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c.jpg',
                'rating': Decimal('4.9'),
                'reviews_count': 42,
                'disponible': True,
            },
            {
                'nombre': 'Kit Integral Alivio Endometriosis',
                'descripcion': 'Kit completo que incluye bolsa térmica, infusión antiinflamatoria, aceite esencial de árnica y guía digital de autocuidado.',
                'composicion': 'Bolsa de semillas, té de jengibre y cúrcuma (50g), aceite de árnica (30ml).',
                'precio': Decimal('95000.00'),
                'marca': 'Florecer',
                'categoria': 'KITS',
                'imagen_url': 'https://images.unsplash.com/photo-1608248597359-f55977fb0b4b?w=500',
                'rating': Decimal('5.0'),
                'reviews_count': 68,
                'disponible': True,
            },
            {
                'nombre': 'Copa Menstrual Anatómica de Silicona Médica',
                'descripcion': 'Copa menstrual hipoalergénica con diseño suave para evitar presión en zonas sensibles durante el ciclo.',
                'composicion': '100% silicona de grado médico platino.',
                'precio': Decimal('62000.00'),
                'marca': 'Luna',
                'categoria': 'COPAS_MENSTRUALES',
                'imagen_url': 'https://m.media-amazon.com/images/I/61p7JcB4u6L._AC_SL1500_.jpg',
                'rating': Decimal('4.7'),
                'reviews_count': 35,
                'disponible': True,
            },
            {
                'nombre': 'Tapete de Yoga Antideslizante Pro',
                'descripcion': 'Tapete acolchado ideal para prácticas de estiramiento suave, yoga restaurativo y posturas de alivio pélvico.',
                'composicion': 'TPE ecológico de alta densidad (6mm de grosor).',
                'precio': Decimal('89900.00'),
                'marca': 'VitalYoga',
                'categoria': 'YOGA_EJERCICIO',
                'imagen_url': 'https://images.unsplash.com/photo-1592417817098-8f3d691a4bf5?w=500',
                'rating': Decimal('4.8'),
                'reviews_count': 29,
                'disponible': True,
            },
            {
                'nombre': 'Libro Digital: Nutrición y Bienestar Hormonal',
                'descripcion': 'Guía práctica escrita por especialistas sobre alimentación antiinflamatoria para la gestión de síntomas de endometriosis.',
                'composicion': 'Formato PDF interactivo (120 páginas con recetas y planes nutricionales).',
                'precio': Decimal('29900.00'),
                'marca': 'Ediciones Bienestar',
                'categoria': 'LIBROS_DIGITALES',
                'imagen_url': 'https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c.jpg',
                'rating': Decimal('4.6'),
                'reviews_count': 51,
                'disponible': True,
            },
            {
                'nombre': 'Parches Térmicos de Alivio Prolongado (Caja x 5)',
                'descripcion': 'Parches de calor autocalentables de hasta 8 horas de duración para llevar bajo la ropa con total comodidad.',
                'composicion': 'Hierro en polvo, carbón activado, sal y agua.',
                'precio': Decimal('34000.00'),
                'marca': 'ThermoAlivio',
                'categoria': 'ALIVIO_DOLOR',
                'imagen_url': 'https://images.unsplash.com/photo-1563089145-599997674d42.jpg',
                'rating': Decimal('4.8'),
                'reviews_count': 44,
                'disponible': True,
            },
            {
                'nombre': 'Kit de Infusiones Botánicas Antiinflamatorias',
                'descripcion': 'Trío de infusiones orgánicas formuladas para reducir la inflamación sistémica y relajar el sistema nervioso.',
                'composicion': 'Té verde con cúrcuma, manzanilla con jengibre y valeriana con pasiflora.',
                'precio': Decimal('42000.00'),
                'marca': 'HerbalVita',
                'categoria': 'KITS',
                'imagen_url': 'https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=500',
                'rating': Decimal('4.9'),
                'reviews_count': 27,
                'disponible': True,
            },
            {
                'nombre': 'Guía de Ejercicios Suave para Suelo Pélvico (E-Book + Audio)',
                'descripcion': 'Programa digital en audio y PDF con rutinas guiadas de relajación y respiración consciente para suelo pélvico.',
                'composicion': 'Archivos PDF y audios MP3 descargables.',
                'precio': Decimal('35000.00'),
                'marca': 'FisioPélvica',
                'categoria': 'LIBROS_DIGITALES',
                'imagen_url': 'https://images.unsplash.com/photo-1584017911766-d451b3d0e843.jpg',
                'rating': Decimal('4.7'),
                'reviews_count': 19,
                'disponible': True,
            },
        ]

        for prod_data in productos_data:
            nombre = prod_data['nombre']
            prod, created = Producto.objects.get_or_create(
                nombre=nombre,
                defaults=prod_data
            )
            if not created:
                for key, val in prod_data.items():
                    setattr(prod, key, val)
                prod.save()
                self.stdout.write(f"Producto actualizado: {prod.nombre}")
            else:
                self.stdout.write(f"Producto creado: {prod.nombre}")

        self.stdout.write(self.style.SUCCESS('¡Poblamiento de bienestar completado exitosamente!'))
