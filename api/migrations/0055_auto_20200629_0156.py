# Generated by Django 3.0.6 on 2020-06-29 01:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0054_tempmatch'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='observers',
            field=models.ManyToManyField(blank=True, related_name='observers', to='api.SC2Profile'),
        ),
    ]