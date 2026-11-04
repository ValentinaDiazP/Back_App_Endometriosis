import os
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
import requests
from bienestar.models import Producto

class Command(BaseCommand):
    help = 'Descarga imágenes desde imagen_url para productos que no tengan imagen guardada'

    def handle(self, *args, **options):
        productos = Producto.objects.filter(imagen__isnull=True).exclude(imagen_url='')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        for producto in productos:
            if not producto.imagen_url:
                continue
            try:
                response = requests.get(producto.imagen_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    nombre_archivo = f"producto_{producto.id}_{os.path.basename(producto.imagen_url.split('?')[0])}"
                    if not nombre_archivo.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                        nombre_archivo += '.jpg'
                    producto.imagen.save(nombre_archivo, ContentFile(response.content), save=True)
                    self.stdout.write(self.style.SUCCESS(f"Imagen descargada y guardada para producto ID {producto.id}"))
                else:
                    self.stdout.write(self.style.WARNING(f"Omitido ID {producto.id}: Código HTTP {response.status_code}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Omitido ID {producto.id} por error: {e}"))
