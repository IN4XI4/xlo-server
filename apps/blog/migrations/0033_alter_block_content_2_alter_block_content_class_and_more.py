# Generated by Django 4.2.6 on 2024-12-04 02:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0032_block_block_color_block_content_2_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='block',
            name='content_2',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='block',
            name='content_class',
            field=models.CharField(blank=True, choices=[('FACT', 'Fact'), ('MYTH', 'Myth'), ('OPINION', 'Opinion')], null=True),
        ),
        migrations.AlterField(
            model_name='block',
            name='quoted_by',
            field=models.CharField(blank=True, max_length=70, null=True),
        ),
        migrations.AlterField(
            model_name='story',
            name='language',
            field=models.CharField(blank=True, choices=[(None, 'Unspecified Language'), ('EN', 'English'), ('ES', 'Spanish'), ('FR', 'French'), ('DE', 'German'), ('IT', 'Italian'), ('PT', 'Portuguese'), ('OT', 'Other')], max_length=2, null=True),
        ),
    ]
