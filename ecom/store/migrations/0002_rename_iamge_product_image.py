# Generated by Django 5.1 on 2024-08-14 21:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("store", "0001_initial"),
    ]

    operations = [
        migrations.RenameField(
            model_name="product",
            old_name="iamge",
            new_name="image",
        ),
    ]
