from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone

from .models import Story, Chapter, StoryNote, StoryAssistance
from .forms import StoryForm, ChapterForm, StoryNoteForm
from characters.models import Character
from core.services.openai_service import OpenAIService

@login_required
def story_list(request):
    """View for listing all stories"""
    # Get filter parameters
    genre = request.GET.get('genre')
    show_archived = request.GET.get('show_archived') == '1'
    
    # Base queryset
    stories = Story.objects.filter(user=request.user)
    
    # Apply filters
    if genre:
        stories = stories.filter(genre=genre)
    
    if not show_archived:
        stories = stories.filter(is_archived=False)
    
    # Get all genres for filter
    all_genres = Story.objects.filter(
        user=request.user,
        genre__isnull=False,
        genre__gt=''
    ).values_list('genre', flat=True).distinct()
    
    # Get statistics
    total_stories = stories.count()
    total_words = sum(story.word_count() for story in stories)
    
    # Get recently updated stories
    recent_stories = stories.order_by('-updated_at')[:5]
    
    # Get completed stories
    completed_stories = stories.filter(is_complete=True)
    
    context = {
        'stories': stories,
        'recent_stories': recent_stories,
        'completed_stories': completed_stories,
        'total_stories': total_stories,
        'total_words': total_words,
        'genres': all_genres,
        'current_genre': genre,
        'show_archived': show_archived,
    }
    
    return render(request, 'stories/story_list.html', context)

@login_required
def story_detail(request, pk):
    """View for displaying a story"""
    story = get_object_or_404(Story, pk=pk, user=request.user)
    
    # Get chapters
    chapters = Chapter.objects.filter(story=story).order_by('order')
    
    # Get notes
    notes = StoryNote.objects.filter(story=story)
    
    # Get characters used in the story
    characters = story.characters.all()
    
    # Get recent assistance
    assistance = StoryAssistance.objects.filter(story=story).order_by('-created_at')[:5]
    
    context = {
        'story': story,
        'chapters': chapters,
        'notes': notes,
        'characters': characters,
        'assistance': assistance,
    }
    
    return render(request, 'stories/story_detail.html', context)

@login_required
def story_create(request):
    """View for creating a new story"""
    if request.method == 'POST':
        form = StoryForm(request.POST)
        if form.is_valid():
            story = form.save(commit=False)
            story.user = request.user
            story.save()
            
            # Save many-to-many relationships
            form.save_m2m()
            
            messages.success(request, f"Story '{story.title}' created successfully!")
            return redirect('stories:detail', pk=story.pk)
    else:
        form = StoryForm()
        
        # Check for a prompt in the query parameters
        prompt = request.GET.get('prompt')
        if prompt:
            form.fields['description'].initial = prompt
    
    # Get available characters for the form
    available_characters = Character.objects.filter(
        user=request.user,
        is_archived=False
    )
    
    context = {
        'form': form,
        'available_characters': available_characters,
        'is_new': True,
    }
    
    return render(request, 'stories/story_form.html', context)

@login_required
def story_edit(request, pk):
    """View for editing a story"""
    story = get_object_or_404(Story, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = StoryForm(request.POST, instance=story)
        if form.is_valid():
            form.save()
            messages.success(request, f"Story '{story.title}' updated successfully!")
            return redirect('stories:detail', pk=story.pk)
    else:
        form = StoryForm(instance=story)
    
    # Get available characters for the form
    available_characters = Character.objects.filter(
        user=request.user,
        is_archived=False
    )
    
    context = {
        'form': form,
        'story': story,
        'available_characters': available_characters,
        'is_new': False,
    }
    
    return render(request, 'stories/story_form.html', context)

@login_required
def story_write(request, pk):
    """View for writing/editing story content"""
    story = get_object_or_404(Story, pk=pk, user=request.user)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content is not None:
            story.content = content
            story.updated_at = timezone.now()
            story.save(update_fields=['content', 'updated_at'])
            messages.success(request, "Story content saved successfully!")
        
        # Check if we're marking as complete
        if request.POST.get('mark_complete'):
            story.is_complete = True
            story.save(update_fields=['is_complete'])
            messages.success(request, f"Story '{story.title}' marked as complete!")
        
        return redirect('stories:write', pk=story.pk)
    
    # Get characters for assistance features
    characters = story.characters.all()
    
    context = {
        'story': story,
        'characters': characters,
    }
    
    return render(request, 'stories/story_write.html', context)

@login_required
def story_assistance(request, pk):
    """API view for getting AI assistance with writing"""
    story = get_object_or_404(Story, pk=pk, user=request.user)
    
    if request.method == 'POST':
        assistance_type = request.POST.get('assistance_type')
        prompt = request.POST.get('prompt')
        context = request.POST.get('context', '')
        character_id = request.POST.get('character_id')
        
        if not prompt:
            return JsonResponse({'error': 'Prompt is required'}, status=400)
        
        try:
            # Get character if provided
            character = None
            if character_id:
                character = get_object_or_404(Character, pk=character_id, user=request.user)
            
            # Create OpenAI service
            openai_service = OpenAIService(request.user)
            
            # Generate assistance based on type
            if assistance_type == 'plot_suggestion':
                response = openai_service.generate_plot_suggestion(story, prompt, context)
            elif assistance_type == 'character_dialogue' and character:
                response = openai_service.generate_character_dialogue(story, character, prompt, context)
            elif assistance_type == 'description':
                response = openai_service.generate_description(story, prompt, context)
            elif assistance_type == 'continuation':
                response = openai_service.continue_story(story, prompt, context)
            elif assistance_type == 'editing':
                response = openai_service.edit_story_section(story, prompt, context)
            else:
                response = openai_service.generate_general_assistance(story, prompt, context)
            
            # Create log of assistance
            assistance = StoryAssistance.objects.create(
                story=story,
                assistance_type=assistance_type,
                user_prompt=prompt,
                ai_response=response['content'],
                prompt_tokens=response['token_usage'].get('prompt_tokens', 0),
                completion_tokens=response['token_usage'].get('completion_tokens', 0)
            )
            
            # Add tokens to story usage
            story.add_tokens(assistance.total_tokens)
            
            return JsonResponse({
                'id': assistance.id,
                'content': response['content'],
                'tokens_used': assistance.total_tokens
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def story_archive(request, pk):
    """View for archiving a story"""
    story = get_object_or_404(Story, pk=pk, user=request.user)
    
    if request.method == 'POST':
        story.is_archived = True
        story.save(update_fields=['is_archived'])
        
        messages.success(request, f"Story '{story.title}' archived successfully!")
        return redirect('stories:list')
    
    context = {
        'story': story,
    }
    
    return render(request, 'stories/story_confirm_archive.html', context)

@login_required
def story_unarchive(request, pk):
    """View for unarchiving a story"""
    story = get_object_or_404(Story, pk=pk, user=request.user)
    
    if request.method == 'POST':
        story.is_archived = False
        story.save(update_fields=['is_archived'])
        
        messages.success(request, f"Story '{story.title}' unarchived successfully!")
        return redirect('stories:detail', pk=story.pk)
    
    context = {
        'story': story,
    }
    
    return render(request, 'stories/story_confirm_unarchive.html', context)

@login_required
def story_delete(request, pk):
    """View for deleting a story"""
    story = get_object_or_404(Story, pk=pk, user=request.user)
    
    if request.method == 'POST':
        title = story.title
        story.delete()
        
        messages.success(request, f"Story '{title}' deleted successfully!")
        return redirect('stories:list')
    
    context = {
        'story': story,
    }
    
    return render(request, 'stories/story_confirm_delete.html', context)

@login_required
def chapter_create(request, story_pk):
    """View for creating a new chapter"""
    story = get_object_or_404(Story, pk=story_pk, user=request.user)
    
    if request.method == 'POST':
        form = ChapterForm(request.POST)
        if form.is_valid():
            chapter = form.save(commit=False)
            chapter.story = story
            
            # Set order to be the next in sequence
            last_chapter = Chapter.objects.filter(story=story).order_by('-order').first()
            chapter.order = 1 if not last_chapter else last_chapter.order + 1
            
            chapter.save()
            
            # Save many-to-many relationships
            form.save_m2m()
            
            messages.success(request, f"Chapter '{chapter.title}' created successfully!")
            return redirect('stories:detail', pk=story.pk)
    else:
        form = ChapterForm()
    
    context = {
        'form': form,
        'story': story,
    }
    
    return render(request, 'stories/chapter_form.html', context)

@login_required
def chapter_edit(request, story_pk, chapter_pk):
    """View for editing a chapter"""
    story = get_object_or_404(Story, pk=story_pk, user=request.user)
    chapter = get_object_or_404(Chapter, pk=chapter_pk, story=story)
    
    if request.method == 'POST':
        form = ChapterForm(request.POST, instance=chapter)
        if form.is_valid():
            form.save()
            messages.success(request, f"Chapter '{chapter.title}' updated successfully!")
            return redirect('stories:detail', pk=story.pk)
    else:
        form = ChapterForm(instance=chapter)
    
    context = {
        'form': form,
        'story': story,
        'chapter': chapter,
    }
    
    return render(request, 'stories/chapter_form.html', context)

@login_required
def note_create(request, story_pk):
    """View for creating a new story note"""
    story = get_object_or_404(Story, pk=story_pk, user=request.user)
    
    if request.method == 'POST':
        form = StoryNoteForm(request.POST)
        if form.is_valid():
            note = form.save(commit=False)
            note.story = story
            note.save()
            
            messages.success(request, f"Note '{note.title}' created successfully!")
            return redirect('stories:detail', pk=story.pk)
    else:
        form = StoryNoteForm()
    
    # Get available characters for the form
    available_characters = Character.objects.filter(
        user=request.user,
        is_archived=False
    )
    
    context = {
        'form': form,
        'story': story,
        'available_characters': available_characters,
    }
    
    return render(request, 'stories/note_form.html', context)

@login_required
def note_edit(request, story_pk, note_pk):
    """View for editing a story note"""
    story = get_object_or_404(Story, pk=story_pk, user=request.user)
    note = get_object_or_404(StoryNote, pk=note_pk, story=story)
    
    if request.method == 'POST':
        form = StoryNoteForm(request.POST, instance=note)
        if form.is_valid():
            form.save()
            messages.success(request, f"Note '{note.title}' updated successfully!")
            return redirect('stories:detail', pk=story.pk)
    else:
        form = StoryNoteForm(instance=note)
    
    # Get available characters for the form
    available_characters = Character.objects.filter(
        user=request.user,
        is_archived=False
    )
    
    context = {
        'form': form,
        'story': story,
        'note': note,
        'available_characters': available_characters,
    }
    
    return render(request, 'stories/note_form.html', context)

@login_required
def note_delete(request, story_pk, note_pk):
    """View for deleting a story note"""
    story = get_object_or_404(Story, pk=story_pk, user=request.user)
    note = get_object_or_404(StoryNote, pk=note_pk, story=story)
    
    if request.method == 'POST':
        title = note.title
        note.delete()
        
        messages.success(request, f"Note '{title}' deleted successfully!")
        return redirect('stories:detail', pk=story.pk)
    
    context = {
        'story': story,
        'note': note,
    }
    
    return render(request, 'stories/note_confirm_delete.html', context)