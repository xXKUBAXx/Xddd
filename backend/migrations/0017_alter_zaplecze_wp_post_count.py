# Generated by Django 4.2.4 on 2023-12-29 11:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0016_alter_account_openai_api_key_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='zaplecze',
            name='wp_post_count',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]