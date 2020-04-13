# Generated by Django 3.0.3 on 2020-02-13 04:18

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0022_auto_20200205_0553'),
    ]

    operations = [
        migrations.CreateModel(
            name='TwitchStream',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False, unique=True)),
                ('user_name', models.CharField(max_length=300)),
                ('active', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
