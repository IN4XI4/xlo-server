# Generated by Django 4.2.6 on 2024-02-23 21:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0008_alter_comment_created_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='like',
            name='created_time',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='like',
            name='updated_time',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
