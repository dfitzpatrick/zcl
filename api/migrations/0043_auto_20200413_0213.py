# Generated by Django 3.0.4 on 2020-04-13 02:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0042_auto_20200412_2328'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='replay',
            name='profile',
        ),
        migrations.AddField(
            model_name='replay',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
        ),
    ]
