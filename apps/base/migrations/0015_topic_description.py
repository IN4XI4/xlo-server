# Generated by Django 4.2.6 on 2024-11-07 22:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0014_mentor_created_by_mentor_user_alter_mentor_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='description',
            field=models.CharField(blank=True, max_length=400),
        ),
    ]
