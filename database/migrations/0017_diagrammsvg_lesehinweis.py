# Generated by Django 3.2.8 on 2023-04-14 20:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0016_auto_20230402_2122'),
    ]

    operations = [
        migrations.AddField(
            model_name='diagrammsvg',
            name='lesehinweis',
            field=models.CharField(blank=True, max_length=1000, null=True),
        ),
    ]
