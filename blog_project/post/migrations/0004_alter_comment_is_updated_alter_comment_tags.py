# Generated by Django 4.1.2 on 2022-10-22 06:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('post', '0003_alter_comment_is_updated'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='is_updated',
            field=models.BooleanField(default=False, null=True),
        ),
        migrations.AlterField(
            model_name='comment',
            name='tags',
            field=models.ManyToManyField(blank=True, related_name='tag_by_comment', to='post.tag'),
        ),
    ]
