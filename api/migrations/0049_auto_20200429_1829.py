# Generated by Django 3.0.5 on 2020-04-29 18:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0048_auto_20200428_0700'),
    ]

    operations = [
        migrations.AddField(
            model_name='sc2profile',
            name='clan_name',
            field=models.CharField(blank=True, default='', max_length=300),
        ),
        migrations.AddField(
            model_name='sc2profile',
            name='clan_tag',
            field=models.CharField(blank=True, default='', max_length=50),
        ),
    ]