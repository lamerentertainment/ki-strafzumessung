# Generated by Django 5.0.2 on 2025-03-15 16:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0031_alter_betmurteil_options_and_more'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='HauptdeliktTatmittel',
            new_name='Tatmittel',
        ),
    ]
