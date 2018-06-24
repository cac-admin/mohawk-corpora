# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-06-22 23:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('transcription', '0008_auto_20180622_2244'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='audiofiletranscription',
            options={'verbose_name': 'Audio File Transcription', 'verbose_name_plural': 'Audio File Transcriptions'},
        ),
        migrations.AlterField(
            model_name='transcriptionsegment',
            name='edited_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='people.Person'),
        ),
        migrations.AlterField(
            model_name='transcriptionsegment',
            name='text',
            field=models.CharField(blank=True, help_text='The initial transcribed text', max_length=1024, null=True),
        ),
    ]
