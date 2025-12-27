from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dockspace', '0005_alter_mailaccount_last_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='mailgroup',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
        migrations.AddField(
            model_name='mailgroup',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, null=True),
        ),
    ]
