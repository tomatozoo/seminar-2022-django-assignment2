# Generated by Django 4.1.2 on 2022-10-20 06:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('post', '0003_alter_post_n_min_read'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='tag',
            field=models.ManyToManyField(null=True, related_name='tag_by_post', to='post.tag'),
        ),
    ]