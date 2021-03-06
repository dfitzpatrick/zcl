# Generated by Django 3.0.1 on 2019-12-23 00:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_auto_20191222_2337'),
    ]

    operations = [
        migrations.AlterField(
            model_name='replay',
            name='match',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='replay', to='api.Match'),
        ),
        migrations.AlterField(
            model_name='replay',
            name='profile',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='api.SC2Profile'),
        ),
    ]
