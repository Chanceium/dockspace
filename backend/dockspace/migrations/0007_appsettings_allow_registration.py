from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dockspace', '0006_mailgroup_timestamps'),
    ]

    operations = [
        migrations.AddField(
            model_name='appsettings',
            name='allow_registration',
            field=models.BooleanField(default=False, help_text='Allow self-service registration at /register after setup'),
        ),
    ]
