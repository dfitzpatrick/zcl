# Generated by Django 3.0.6 on 2020-05-12 01:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0008_apptoken'),
    ]

    operations = [
        migrations.AddField(
            model_name='discorduser',
            name='client_heartbeat',
            field=models.DateTimeField(null=True),
        ),
    ]