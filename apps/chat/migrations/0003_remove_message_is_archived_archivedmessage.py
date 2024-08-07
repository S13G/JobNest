# Generated by Django 5.0.4 on 2024-07-07 21:59

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('chat', '0002_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='message',
            name='is_archived',
        ),
        migrations.CreateModel(
            name='ArchivedMessage',
            fields=[
                ('id',
                 models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('created', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated', models.DateTimeField(auto_now=True, null=True)),
                ('message',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='archived_by_users',
                                   to='chat.message')),
                ('user',
                 models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='archived_messages',
                                   to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'message')},
            },
        ),
    ]
