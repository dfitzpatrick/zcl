# Generated by Django 3.0.4 on 2020-04-05 06:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0033_auto_20200405_0553'),
    ]

    operations = [
        migrations.AddField(
            model_name='match',
            name='game_length',
            field=models.FloatField(default=0),
        ),
    ]
