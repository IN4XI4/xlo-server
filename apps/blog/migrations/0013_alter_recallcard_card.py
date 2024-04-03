# Generated by Django 4.2.6 on 2024-03-26 23:16

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0012_recallcard'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recallcard',
            name='card',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='card', to='blog.card'),
        ),
    ]
