# Generated by Django 4.2.6 on 2023-11-17 21:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0002_topictag_topic_tag'),
        ('blog', '0003_alter_story_options'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='card',
            name='content',
        ),
        migrations.RemoveField(
            model_name='card',
            name='image',
        ),
        migrations.RemoveField(
            model_name='card',
            name='monster',
        ),
        migrations.AddField(
            model_name='block',
            name='order',
            field=models.IntegerField(blank=True, default=0),
        ),
        migrations.AddField(
            model_name='card',
            name='defense_color',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='card',
            name='soft_skill',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='base.softskill'),
        ),
    ]
