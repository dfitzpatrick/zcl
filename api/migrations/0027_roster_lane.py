# Generated by Django 3.0.4 on 2020-03-29 20:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0026_match_details'),
    ]

    operations = [
        migrations.AddField(
            model_name='roster',
            name='lane',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='api.SC2Profile'),
        ),
    ]
