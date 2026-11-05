import django.db.models.deletion
from django.db import migrations, models

AYUDA_TEXTO = 'Formato: deja una línea en blanco entre párrafos. **texto** = negrita, __texto__ = subrayado, [texto](https://enlace) = enlace, líneas que empiezan con "- " = lista, "## " = subtítulo.'


class Migration(migrations.Migration):

    dependencies = [
        ('educativo', '0013_ejercicios_premium'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contenidoeducativo',
            name='cuerpo',
            field=models.TextField(help_text=AYUDA_TEXTO),
        ),
        migrations.AddField(
            model_name='contenidoeducativo',
            name='imagen',
            field=models.ImageField(blank=True, null=True, upload_to='educativo/', verbose_name='imagen'),
        ),
        migrations.AddField(
            model_name='contenidoeducativo',
            name='pie_de_imagen',
            field=models.CharField(blank=True, max_length=200, verbose_name='pie de imagen'),
        ),
        migrations.CreateModel(
            name='PasoModuloGuiado',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orden', models.PositiveSmallIntegerField(default=1, help_text='Posición del paso (1, 2, 3…).')),
                ('titulo', models.CharField(max_length=200)),
                ('texto', models.TextField(help_text=AYUDA_TEXTO)),
                ('punto_clave', models.CharField(blank=True, help_text='Idea clave resaltada al final del paso (opcional).', max_length=300)),
                ('ejercicio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='pasos_modulo', to='educativo.ejerciciopsicoeducativo')),
            ],
            options={
                'verbose_name': 'paso de módulo guiado',
                'verbose_name_plural': 'pasos de módulo guiado',
                'ordering': ['ejercicio', 'orden', 'id'],
            },
        ),
        migrations.CreateModel(
            name='IndicacionPractica',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orden', models.PositiveSmallIntegerField(default=1, help_text='Posición de la indicación (1, 2, 3…).')),
                ('texto', models.CharField(max_length=300)),
                ('ejercicio', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='indicaciones', to='educativo.ejerciciopsicoeducativo')),
            ],
            options={
                'verbose_name': 'indicación de práctica guiada',
                'verbose_name_plural': 'indicaciones de práctica guiada',
                'ordering': ['ejercicio', 'orden', 'id'],
            },
        ),
    ]
