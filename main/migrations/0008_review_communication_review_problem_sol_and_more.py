# Generated by Django 4.2.1 on 2023-06-22 17:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0007_remove_review_review_rating_content_1_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='communication',
            field=models.TextField(default=2, max_length=400),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='review',
            name='problem_sol',
            field=models.TextField(default=2, max_length=400),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='review',
            name='sociability',
            field=models.TextField(default=3, max_length=400),
            preserve_default=False,
        ),
    ]
