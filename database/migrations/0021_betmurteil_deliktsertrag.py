# Generated by Django 3.2.8 on 2023-04-20 19:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0020_betmurteil_vollzug'),
    ]

    operations = [
        migrations.AddField(
            model_name='betmurteil',
            name='deliktsertrag',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
