# Generated by Django 5.0.4 on 2025-03-15 18:34

import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('characters', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConversationSummary',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField(help_text='Summarized content')),
                ('token_count', models.IntegerField(default=0, help_text='Tokens in this summary')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['created_at'],
            },
        ),
        migrations.CreateModel(
            name='Message',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.TextField()),
                ('sender', models.CharField(choices=[('user', 'User'), ('character', 'Character'), ('system', 'System')], max_length=20)),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional metadata about the message')),
                ('prompt_tokens', models.IntegerField(default=0, help_text='Tokens used in the prompt')),
                ('completion_tokens', models.IntegerField(default=0, help_text='Tokens used in the completion')),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
                ('is_read', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ['timestamp'],
            },
        ),
        migrations.CreateModel(
            name='Conversation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(blank=True, max_length=200)),
                ('context', models.TextField(blank=True, help_text='Optional context for the conversation')),
                ('total_tokens', models.IntegerField(default=0, help_text='Total tokens used in this conversation')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_archived', models.BooleanField(default=False)),
                ('character', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='conversations', to='characters.character')),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
    ]
