from django.core.management.base import BaseCommand

from educativo.contenido_compartido import ARCHIVO, guardar


class Command(BaseCommand):
    help = (
        'Guarda el contenido del gestor (Educativo) en '
        'educativo/contenido/contenido_educativo.json para compartirlo por git.'
    )

    def handle(self, *args, **options):
        datos = guardar()
        resumen = ', '.join(
            f'{len(datos[k])} {k}' for k in ('contenidos', 'ejercicios', 'rutas')
        )
        self.stdout.write(self.style.SUCCESS(f'Contenido exportado ({resumen}) en {ARCHIVO}'))
        self.stdout.write(
            'Sube a git este archivo y las imágenes nuevas de media/educativo/. '
            'Las demás lo cargan con: python manage.py importar_contenido_educativo'
        )
