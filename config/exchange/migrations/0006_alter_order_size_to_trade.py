# Generated by Django 5.0.3 on 2024-03-26 20:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('exchange', '0005_order_size_to_trade'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='size_to_trade',
            field=models.DecimalField(decimal_places=4, max_digits=7),
        ),
    ]
