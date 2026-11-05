from django.core.management.base import BaseCommand, CommandError

from educativo.contenido_compartido import ARCHIVO, cargar


class Command(BaseCommand):
    help = (
        'Carga en tu base de datos el contenido del gestor (Educativo) guardado en '
        'educativo/contenido/contenido_educativo.json.'
    )

    def handle(self, *args, **options):
        if not ARCHIVO.exists():
            raise CommandError(
                f'No existe {ARCHIVO}. Alguien debe correr primero exportar_contenido_educativo.'
            )
        resumen = cargar()
        detalle = ', '.join(f'{n} {k}' for k, n in resumen.items())
        self.stdout.write(self.style.SUCCESS(f'Contenido importado: {detalle}.'))
