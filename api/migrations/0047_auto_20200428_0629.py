# Generated by Django 3.0.5 on 2020-04-28 06:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0046_auto_20200427_1748'),
    ]

    operations = [
        migrations.AlterField(
            model_name='match',
            name='id',
            field=models.CharField(max_length=50, primary_key=True, serialize=False, unique=True),
        ),
    ]
