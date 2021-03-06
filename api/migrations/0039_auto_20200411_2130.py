# Generated by Django 3.0.4 on 2020-04-11 21:30

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0038_auto_20200406_0140'),
    ]

    operations = [
        migrations.AddField(
            model_name='segment',
            name='valid',
            field=models.BooleanField(default=True),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='sc2profile',
            name='discord_users',
            field=models.ManyToManyField(related_name='profiles', to=settings.AUTH_USER_MODEL),
        ),
    ]
