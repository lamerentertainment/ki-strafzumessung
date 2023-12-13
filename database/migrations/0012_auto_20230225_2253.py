# Generated by Django 3.2.8 on 2023-02-25 21:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0011_auto_20230219_1604'),
    ]

    operations = [
        migrations.CreateModel(
            name='KIModelPickleFile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30)),
                ('file', models.FileField(upload_to='media')),
            ],
        ),
        migrations.AlterModelOptions(
            name='urteil',
            options={'ordering': ['urteilsdatum'], 'verbose_name_plural': 'Urteile'},
        ),
    ]