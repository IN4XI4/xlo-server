# Generated by Django 4.2.6 on 2023-11-23 20:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0003_delete_monster_alter_topictag_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='mentor',
            name='color',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
