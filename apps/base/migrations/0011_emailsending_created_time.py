# Generated by Django 4.2.6 on 2024-05-06 03:42

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0010_emailsending'),
    ]

    operations = [
        migrations.AddField(
            model_name='emailsending',
            name='created_time',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
