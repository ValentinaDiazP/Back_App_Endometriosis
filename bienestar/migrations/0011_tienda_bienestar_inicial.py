from django.db import migrations, models
from django.conf import settings

def crear_productos_iniciales(apps, schema_editor):
    Producto = apps.get_model('bienestar', 'Producto')
    productos = [
        {
            "nombre": "Copa Menstrual",
            "descripcion": "Copa menstrual de silicona médica hipoalergénica. Cómoda, reutilizable y ecológica.",
            "precio": 79900.00,
            "marca": "Vital",
            "categoria": "COPAS_MENSTRUALES",
            "imagen_url": "https://images.unsplash.com/photo-1584017911766-d451b3d0e843?w=500",
            "disponible": True
        },
        {
            "nombre": "Kit Menstrual Antiinflamatorio",
            "descripcion": "Incluye infusión botánica relajante, aceite esencial de lavanda y parches térmicos.",
            "precio": 54900.00,
            "marca": "Vital",
            "categoria": "KITS",
            "imagen_url": "https://images.unsplash.com/photo-1608248597359-f55977fb0b4b?w=500",
            "disponible": True
        },
        {
            "nombre": "Peluche Térmico para Cólicos",
            "descripcion": "Peluche terapéutico relleno de semillas naturales y lavanda para calentar en microondas.",
            "precio": 45000.00,
            "marca": "Vital",
            "categoria": "ALIVIO_DOLOR",
            "imagen_url": "https://images.unsplash.com/photo-1563089145-599997674d42?w=500",
            "disponible": True
        },
        {
            "nombre": "Tapete de Yoga Antideslizante",
            "descripcion": "Tapete ecológico de alta densidad ideal para estiramientos y posturas de yoga.",
            "precio": 89900.00,
            "marca": "Vital",
            "categoria": "YOGA_EJERCICIO",
            "imagen_url": "https://images.unsplash.com/photo-1592417817098-8f3d691a4bf5?w=500",
            "disponible": True
        },
        {
            "nombre": "Libro Digital: Nutrición y Endometriosis",
            "descripcion": "Guía completa con recetas antiinflamatorias y hábitos nutricionales recomendados por especialistas.",
            "precio": 29900.00,
            "marca": "Vital",
            "categoria": "LIBROS_DIGITALES",
            "imagen_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=500",
            "disponible": True
        }
    ]

    for p in productos:
        Producto.objects.get_or_create(
            nombre=p["nombre"],
            defaults=p
        )

class Migration(migrations.Migration):

    dependencies = [
        ('bienestar', '0010_citamedica_disponibilidadprofesional'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Producto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200, verbose_name='Nombre del Producto')),
                ('descripcion', models.TextField(verbose_name='Descripción')),
                ('precio', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Precio')),
                ('marca', models.CharField(default='Vital', max_length=100, verbose_name='Marca Aliada')),
                ('categoria', models.CharField(choices=[('COPAS_MENSTRUALES', 'Copas Menstruales'), ('KITS', 'Kits'), ('ALIVIO_DOLOR', 'Alivio del Dolor'), ('YOGA_EJERCICIO', 'Yoga y Ejercicio'), ('LIBROS_DIGITALES', 'Libros Digitales')], max_length=50, verbose_name='Categoría')),
                ('imagen_url', models.URLField(max_length=500, verbose_name='URL de Imagen')),
                ('disponible', models.BooleanField(default=True, verbose_name='Disponible')),
            ],
            options={
                'verbose_name': 'Producto',
                'verbose_name_plural': 'Productos',
            },
        ),
        migrations.CreateModel(
            name='OrdenCompra',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Total Pagado')),
                ('completada', models.BooleanField(default=True, verbose_name='Completada')),
                ('fecha_compra', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Compra')),
                ('items_snapshot', models.TextField(blank=True, default='', verbose_name='Resumen de Productos')),
                ('usuario', models.ForeignKey(on_delete=models.CASCADE, related_name='ordenes_compra', to=settings.AUTH_USER_MODEL, verbose_name='Usuaria')),
            ],
            options={
                'verbose_name': 'Orden de Compra',
                'verbose_name_plural': 'Órdenes de Compra',
                'ordering': ['-fecha_compra'],
            },
        ),
        migrations.CreateModel(
            name='ItemCarrito',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.PositiveIntegerField(default=1, verbose_name='Cantidad')),
                ('agregado_en', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de agregado')),
                ('usuario', models.ForeignKey(on_delete=models.CASCADE, related_name='carrito_items', to=settings.AUTH_USER_MODEL, verbose_name='Usuaria')),
                ('producto', models.ForeignKey(on_delete=models.CASCADE, to='bienestar.producto', verbose_name='Producto')),
            ],
            options={
                'verbose_name': 'Item de Carrito',
                'verbose_name_plural': 'Items de Carrito',
            },
        ),
        migrations.RunPython(crear_productos_iniciales),
    ]
