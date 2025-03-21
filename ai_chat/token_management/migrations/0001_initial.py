# Generated by Django 5.0.4 on 2025-03-15 18:34

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='TokenAlert',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('threshold', models.IntegerField(choices=[(50, '50% of limit'), (80, '80% of limit'), (95, '95% of limit'), (100, '100% of limit (limit reached)')])),
                ('is_acknowledged', models.BooleanField(default=False)),
                ('usage_at_alert', models.IntegerField()),
                ('limit_at_alert', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('acknowledged_at', models.DateTimeField(blank=True, null=True)),
                ('month', models.IntegerField(editable=False)),
                ('year', models.IntegerField(editable=False)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TokenPurchase',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tokens_purchased', models.IntegerField()),
                ('amount_paid', models.DecimalField(decimal_places=2, max_digits=10)),
                ('currency', models.CharField(default='USD', max_length=3)),
                ('payment_provider', models.CharField(default='stripe', max_length=20)),
                ('payment_id', models.CharField(blank=True, max_length=100)),
                ('payment_status', models.CharField(default='pending', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('completed_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TokenUsage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('feature', models.CharField(choices=[('character_creation', 'Character Creation'), ('character_chat', 'Character Chat'), ('story_assistance', 'Story Assistance'), ('memory_summarization', 'Memory Summarization'), ('world_building', 'World Building'), ('plot_development', 'Plot Development'), ('character_development', 'Character Development'), ('other', 'Other')], max_length=30)),
                ('tokens_used', models.IntegerField()),
                ('character_id', models.IntegerField(blank=True, null=True)),
                ('conversation_id', models.IntegerField(blank=True, null=True)),
                ('story_id', models.IntegerField(blank=True, null=True)),
                ('world_id', models.IntegerField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='UserTokenLimit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('monthly_limit', models.PositiveIntegerField(default=100)),
                ('alert_threshold', models.PositiveIntegerField(default=80)),
                ('last_reset', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
    ]
