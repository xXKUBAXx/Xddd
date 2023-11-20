# Generated by Django 4.2.4 on 2023-11-20 08:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0010_alter_zaplecze_domain'),
    ]

    operations = [
        migrations.CreateModel(
            name='Links',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.CharField(max_length=64)),
                ('domain', models.CharField(max_length=64)),
                ('link', models.CharField(max_length=256)),
                ('keyword', models.CharField(max_length=128)),
                ('url', models.CharField(max_length=128)),
                ('cost', models.IntegerField(blank=True, null=True)),
                ('done', models.BooleanField()),
            ],
        ),
    ]