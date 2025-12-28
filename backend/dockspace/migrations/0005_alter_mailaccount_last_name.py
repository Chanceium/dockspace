from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dockspace', '0004_alter_mailaccount_picture'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mailaccount',
            name='last_name',
            field=models.CharField(blank=True, default='', help_text='Family name', max_length=150),
        ),
    ]
