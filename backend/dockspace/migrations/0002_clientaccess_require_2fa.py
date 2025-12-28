# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dockspace', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientaccess',
            name='require_2fa',
            field=models.BooleanField(default=False, help_text='Require two-factor authentication (TOTP) for this client'),
        ),
    ]
