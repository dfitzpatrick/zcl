# Generated by Django 3.0.5 on 2020-05-09 20:30

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0050_auto_20200509_2014'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='MatchMessages',
            new_name='MatchMessage',
        ),
    ]