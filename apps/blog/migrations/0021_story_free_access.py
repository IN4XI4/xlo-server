# Generated by Django 4.2.6 on 2024-04-23 21:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0020_alter_story_slug'),
    ]

    operations = [
        migrations.AddField(
            model_name='story',
            name='free_access',
            field=models.BooleanField(default=False),
        ),
    ]