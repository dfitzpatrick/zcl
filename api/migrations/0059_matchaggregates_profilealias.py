# Generated by Django 3.0.8 on 2020-12-29 05:03

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0058_auto_20201225_0322'),
    ]

    operations = [
        migrations.CreateModel(
            name='ProfileAlias',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_created=True, auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('name', models.CharField(max_length=300)),
                ('profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='aliases', to='api.SC2Profile')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MatchAggregates',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nukes', models.IntegerField(default=0)),
                ('tanks', models.IntegerField(default=0)),
                ('turrets', models.IntegerField(default=0)),
                ('bunkers', models.IntegerField(default=0)),
                ('scv', models.IntegerField(default=0)),
                ('sensors', models.IntegerField(default=0)),
                ('shields', models.IntegerField(default=0)),
                ('supply_depots', models.IntegerField(default=0)),
                ('names', models.CharField(blank=True, default='', max_length=300)),
                ('winners', models.CharField(blank=True, default='', max_length=200)),
                ('mid', models.BooleanField(default=False)),
                ('match', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='aggregates', to='api.Match')),
            ],
        ),
    ]
