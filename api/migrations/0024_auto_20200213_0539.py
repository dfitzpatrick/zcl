# Generated by Django 3.0.3 on 2020-02-13 05:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0023_twitchstream'),
    ]

    operations = [
        migrations.AddField(
            model_name='twitchstream',
            name='uuid',
            field=models.UUIDField(default='a544917d-995d-4fbb-90d0-8ecdd42aacb2'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='twitchstream',
            name='id',
            field=models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
