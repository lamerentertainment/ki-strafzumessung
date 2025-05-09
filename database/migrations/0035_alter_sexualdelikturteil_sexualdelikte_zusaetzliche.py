# Generated by Django 5.0.2 on 2025-03-17 14:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('database', '0034_sexualdelikturteil_hauptdelikt_deliktsdauer_bekannt_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sexualdelikturteil',
            name='sexualdelikte_zusaetzliche',
            field=models.ManyToManyField(blank=True, help_text='weitere Sexualdelikte im Urteilsspruch', related_name='sexualdelikte', to='database.zusaetzlichesexualdelikte'),
        ),
    ]
