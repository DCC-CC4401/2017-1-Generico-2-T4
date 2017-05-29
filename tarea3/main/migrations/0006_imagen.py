# -*- coding: utf-8 -*-
# Generated by Django 1.11.1 on 2017-05-29 02:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_auto_20170528_0436'),
    ]

    operations = [
        migrations.CreateModel(
            name='Imagen',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('imagen', models.ImageField(upload_to='avatars')),
            ],
            options={
                'db_table': 'imagen',
            },
        ),
    ]
