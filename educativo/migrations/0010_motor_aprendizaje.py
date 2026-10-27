import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('educativo', '0009_alter_interaccioncontenido_id_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ReglaAprendizaje',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('clave', models.CharField(max_length=50, unique=True)),
                ('descripcion', models.CharField(max_length=150)),
                ('puntos', models.PositiveIntegerField()),
                ('activa', models.BooleanField(default=True)),
            ],
            options={
                'verbose_name': 'regla de puntos de aprendizaje',
                'verbose_name_plural': 'reglas de puntos de aprendizaje',
                'ordering': ['clave'],
            },
        ),
        migrations.CreateModel(
            name='NivelAprendizaje',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=50)),
                ('puntos_minimos', models.PositiveIntegerField(unique=True)),
                ('emoji', models.CharField(blank=True, max_length=8)),
            ],
            options={
                'verbose_name': 'nivel de aprendizaje',
                'verbose_name_plural': 'niveles de aprendizaje',
                'ordering': ['puntos_minimos'],
            },
        ),
        migrations.CreateModel(
            name='InsigniaRuta',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=100)),
                ('descripcion', models.CharField(blank=True, max_length=200)),
                ('emoji', models.CharField(blank=True, max_length=8)),
                ('ruta', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='insignia', to='educativo.rutaaprendizaje')),
            ],
            options={
                'verbose_name': 'insignia de ruta',
                'verbose_name_plural': 'insignias de ruta',
                'ordering': ['ruta'],
            },
        ),
        migrations.CreateModel(
            name='ProgresoAprendizaje',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('puntos_totales', models.PositiveIntegerField(default=0)),
                ('racha_actual', models.PositiveIntegerField(default=0)),
                ('racha_maxima', models.PositiveIntegerField(default=0)),
                ('ultimo_dia_activo', models.DateField(blank=True, null=True)),
                ('usuario', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='progreso_aprendizaje', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'progreso de aprendizaje',
                'verbose_name_plural': 'progresos de aprendizaje',
            },
        ),
        migrations.CreateModel(
            name='MovimientoAprendizaje',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateField()),
                ('clave', models.CharField(max_length=50)),
                ('referencia', models.CharField(blank=True, max_length=50)),
                ('motivo', models.CharField(max_length=150)),
                ('puntos', models.PositiveIntegerField()),
                ('creado_en', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='movimientos_aprendizaje', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'movimiento de puntos de aprendizaje',
                'verbose_name_plural': 'movimientos de puntos de aprendizaje',
                'ordering': ['-creado_en'],
            },
        ),
        migrations.CreateModel(
            name='InsigniaObtenida',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha', models.DateTimeField(auto_now_add=True)),
                ('insignia', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='obtenidas', to='educativo.insigniaruta')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='insignias_obtenidas', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'insignia obtenida',
                'verbose_name_plural': 'insignias obtenidas',
                'ordering': ['-fecha'],
            },
        ),
        migrations.AddConstraint(
            model_name='insigniaobtenida',
            constraint=models.UniqueConstraint(fields=('usuario', 'insignia'), name='insignia_obtenida_unica'),
        ),
    ]
