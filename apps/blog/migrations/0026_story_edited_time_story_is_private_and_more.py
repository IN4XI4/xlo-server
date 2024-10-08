# Generated by Django 4.2.6 on 2024-09-21 02:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0025_recallcomment'),
    ]

    operations = [
        migrations.AddField(
            model_name='story',
            name='edited_time',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='story',
            name='is_private',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='recallcard',
            name='importance_level',
            field=models.CharField(choices=[('1', 'Important'), ('2', 'Very Important')], default='1', max_length=1),
        ),
    ]
