# Generated manually for Professional.whatsapp

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bienestar', '0007_solicitudcontacto'),
    ]

    operations = [
        migrations.AddField(
            model_name='professional',
            name='whatsapp',
            field=models.CharField(
                blank=True,
                default='',
                help_text='Número con código de país, sin espacios (ej: 573001112233)',
                max_length=20,
                verbose_name='WhatsApp',
            ),
        ),
    ]
