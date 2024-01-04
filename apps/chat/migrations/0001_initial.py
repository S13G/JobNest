# Generated by Django 5.0 on 2024-01-04 00:50

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
                ('text', models.TextField(blank=True, null=True)),
                ('is_read', models.BooleanField(default=False)),
                ('is_archived', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ('-created',),
                'abstract': False,
            },
        ),
    ]
