# Generated by Django 2.2.16 on 2022-07-11 17:18

from django.db import migrations
import users.models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0002_auto_20220629_2212'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='avatar',
            field=users.models.ImageField(blank=True, null=True, upload_to='photos/%Y/%m/%d/'),
        ),
    ]
