# Generated by Django 5.0.4 on 2025-03-15 18:34

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('characters', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StoryAssistance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('assistance_type', models.CharField(choices=[('plot_suggestion', 'Plot Suggestion'), ('character_dialogue', 'Character Dialogue'), ('description', 'Description Enhancement'), ('continuation', 'Story Continuation'), ('editing', 'Editing and Revision'), ('worldbuilding', 'Worldbuilding Detail')], max_length=30)),
                ('user_prompt', models.TextField(help_text="User's request for assistance")),
                ('ai_response', models.TextField(help_text='AI-generated assistance')),
                ('prompt_tokens', models.IntegerField(default=0)),
                ('completion_tokens', models.IntegerField(default=0)),
                ('was_used', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='StoryNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('content', models.TextField(blank=True)),
                ('note_type', models.CharField(choices=[('outline', 'Outline'), ('character_note', 'Character Note'), ('worldbuilding', 'Worldbuilding'), ('plot_idea', 'Plot Idea'), ('research', 'Research'), ('general', 'General Note')], default='general', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-updated_at'],
            },
        ),
        migrations.CreateModel(
            name='Chapter',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('content', models.TextField(blank=True)),
                ('order', models.IntegerField(default=0, help_text='Order of chapter in the story')),
                ('token_usage', models.IntegerField(default=0, help_text='Tokens used in this chapter')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('characters', models.ManyToManyField(blank=True, related_name='chapters', to='characters.character')),
            ],
            options={
                'ordering': ['order', 'created_at'],
            },
        ),
        migrations.CreateModel(
            name='Story',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True, help_text='Brief description of the story')),
                ('content', models.TextField(blank=True, help_text='The story content')),
                ('genre', models.CharField(blank=True, max_length=100)),
                ('is_complete', models.BooleanField(default=False)),
                ('token_usage', models.IntegerField(default=0, help_text='Total tokens used in this story')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_archived', models.BooleanField(default=False)),
                ('is_public', models.BooleanField(default=False)),
                ('characters', models.ManyToManyField(blank=True, related_name='stories', to='characters.character')),
            ],
            options={
                'verbose_name_plural': 'Stories',
                'ordering': ['-updated_at'],
            },
        ),
    ]
