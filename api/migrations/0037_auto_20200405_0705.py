# Generated by Django 3.0.4 on 2020-04-05 07:05

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0036_auto_20200405_0637'),
    ]

    operations = [
        migrations.AlterField(
            model_name='segmentprofileitem',
            name='match',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='match', to='api.Match'),
        ),
    ]
