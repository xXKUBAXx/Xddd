# Generated by Django 4.2.4 on 2024-04-23 07:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0031_alter_primislaodomains_server_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='primislaoLinks',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.CharField(max_length=256)),
                ('link_domain', models.CharField(max_length=256)),
                ('target_domain', models.CharField(max_length=256)),
                ('anchor', models.CharField(max_length=256)),
                ('nofollow', models.BooleanField(blank=True, null=True)),
                ('limit', models.IntegerField(default=0)),
                ('link_id', models.IntegerField(default=0)),
            ],
        ),
    ]
