# Generated manually for SolicitudContacto and Publicacion.es_anonimo verbose_name

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bienestar', '0006_publicacion_es_anonimo'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name='publicacion',
            name='es_anonimo',
            field=models.BooleanField(default=False, verbose_name='Publicación anónima'),
        ),
        migrations.CreateModel(
            name='SolicitudContacto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('fecha_solicitud', models.DateTimeField(auto_now_add=True, verbose_name='Fecha de solicitud')),
                ('estado', models.CharField(
                    choices=[('PENDIENTE', 'Pendiente'), ('ATENDIDA', 'Atendida'), ('CANCELADA', 'Cancelada')],
                    default='PENDIENTE',
                    max_length=20,
                    verbose_name='Estado',
                )),
                ('profesional', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='solicitudes_contacto',
                    to='bienestar.professional',
                    verbose_name='Profesional',
                )),
                ('usuario', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='solicitudes_contacto',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Usuaria',
                )),
            ],
            options={
                'verbose_name': 'Solicitud de contacto',
                'verbose_name_plural': 'Solicitudes de contacto',
                'ordering': ['-fecha_solicitud'],
            },
        ),
    ]
