# Generated by Django 5.0 on 2023-12-30 08:19

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('misc', '0003_faqtype_faq'),
    ]

    operations = [
        migrations.AlterField(
            model_name='faq',
            name='type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='faqs', to='misc.faqtype'),
        ),
    ]