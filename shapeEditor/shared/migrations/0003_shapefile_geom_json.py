# Generated by Django 3.0.2 on 2020-02-03 06:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shared', '0002_auto_20200202_1712'),
    ]

    operations = [
        migrations.AddField(
            model_name='shapefile',
            name='geom_json',
            field=models.TextField(blank=True, null=True),
        ),
    ]