# Generated by Django 4.2.6 on 2023-11-23 20:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0005_alter_story_options_story_views_count'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='card',
            name='defense_color',
        ),
    ]
