# Generated by Django 2.2.5 on 2020-05-05 00:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0002_auto_20200505_0006'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='college',
            field=models.CharField(default=1, max_length=32, verbose_name='学院'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='user',
            name='snum',
            field=models.CharField(default=1, max_length=32, verbose_name='学号'),
            preserve_default=False,
        ),
    ]
