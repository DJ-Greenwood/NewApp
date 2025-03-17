import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Q

from .models import Journal, JournalEntry, JournalTemplate, JournalPrompt
from .forms import JournalForm, JournalEntryForm, JournalTemplateForm, JournalPromptForm
from characters.models import Character

@login_required
def journal_list(request):
    """View for listing all journals"""
    # Get filter parameters
    journal_type = request.GET.get('type')
    character_id = request.GET.get('character')
    show_archived = request.GET.get('show_archived') == '1'
    
    # Base queryset
    journals = Journal.objects.filter(user=request.user)
    
    # Apply filters
    if journal_type:
        journals = journals.filter(journal_type=journal_type)
    
    if character_id:
        journals = journals.filter(character_id=character_id)
    
    if not show_archived:
        journals = journals.filter(is_archived=False)
    
    # Annotate with entry counts for efficiency
    journals = journals.annotate(entry_count=Count('entries'))
    
    # Get journal statistics
    total_journals = journals.count()
    total_entries = JournalEntry.objects.filter(journal__user=request.user).count()
    
    # Get journal types for filter
    journal_types = Journal.JOURNAL_TYPES
    
    # Get characters with journals
    characters_with_journals = Character.objects.filter(
        journals__user=request.user
    ).distinct().order_by('name')
    
    # Get recent entries
    recent_entries = JournalEntry.objects.filter(
        journal__user=request.user,
        journal__is_archived=False
    ).order_by('-entry_date', '-created_at')[:5]
    
    context = {
        'journals': journals,
        'total_journals': total_journals,
        'total_entries': total_entries,
        'journal_types': journal_types,
        'characters': characters_with_journals,
        'recent_entries': recent_entries,
        'filter_journal_type': journal_type,
        'filter_character_id': character_id,
        'show_archived': show_archived,
    }
    
    return render(request, 'journals/journal_list.html', context)

@login_required
def journal_detail(request, pk):
    """View for displaying a journal with its entries"""
    journal = get_object_or_404(Journal, pk=pk, user=request.user)
    
    # Get entries
    entries = JournalEntry.objects.filter(journal=journal).order_by('-entry_date', '-created_at')
    
    # Get character info if it's a character journal
    character = journal.character
    
    # Get filter parameters
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search = request.GET.get('search')
    tag = request.GET.get('tag')
    
    # Apply filters
    if date_from:
        entries = entries.filter(entry_date__gte=date_from)
    
    if date_to:
        entries = entries.filter(entry_date__lte=date_to)
    
    if search:
        entries = entries.filter(
            Q(title__icontains=search) | 
            Q(content__icontains=search)
        )
    
    if tag:
        # Filter by tag in the JSON field
        # This is a simplistic approach; for production, you might want to use JSONField lookups
        filtered_entries = []
        for entry in entries:
            if tag in entry.tags:
                filtered_entries.append(entry.id)
        entries = entries.filter(id__in=filtered_entries)
    
    # Get all tags used in this journal for the filter
    all_tags = set()
    for entry in JournalEntry.objects.filter(journal=journal):
        if entry.tags:
            all_tags.update(entry.tags)
    
    context = {
        'journal': journal,
        'entries': entries,
        'character': character,
        'tags': sorted(all_tags),
        'filter_date_from': date_from,
        'filter_date_to': date_to,
        'filter_search': search,
        'filter_tag': tag,
    }
    
    return render(request, 'journals/journal_detail.html', context)

@login_required
def journal_create(request):
    """View for creating a new journal"""
    if request.method == 'POST':
        form = JournalForm(request.POST)
        if form.is_valid():
            journal = form.save(commit=False)
            journal.user = request.user
            journal.save()
            
            messages.success(request, f"Journal '{journal.title}' created successfully!")
            return redirect('journals:detail', pk=journal.pk)
    else:
        form = JournalForm()
        
        # Check for a character ID in the query parameters
        character_id = request.GET.get('character')
        if character_id:
            try:
                character = Character.objects.get(pk=character_id, user=request.user)
                form.fields['character'].initial = character.id
                form.fields['journal_type'].initial = 'character'
                form.fields['title'].initial = f"{character.name}'s Journal"
            except Character.DoesNotExist:
                pass
    
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
    
    return render(request, 'journals/journal_form.html', context)

@login_required
def journal_edit(request, pk):
    """View for editing a journal"""
    journal = get_object_or_404(Journal, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = JournalForm(request.POST, instance=journal)
        if form.is_valid():
            form.save()
            messages.success(request, f"Journal '{journal.title}' updated successfully!")
            return redirect('journals:detail', pk=journal.pk)
    else:
        form = JournalForm(instance=journal)
    
    # Get available characters for the form
    available_characters = Character.objects.filter(
        user=request.user,
        is_archived=False
    )
    
    context = {
        'form': form,
        'journal': journal,
        'available_characters': available_characters,
        'is_new': False,
    }
    
    return render(request, 'journals/journal_form.html', context)

@login_required
def journal_archive(request, pk):
    """View for archiving a journal"""
    journal = get_object_or_404(Journal, pk=pk, user=request.user)
    
    if request.method == 'POST':
        journal.is_archived = True
        journal.save(update_fields=['is_archived'])
        
        messages.success(request, f"Journal '{journal.title}' archived successfully!")
        return redirect('journals:list')
    
    context = {
        'journal': journal,
    }
    
    return render(request, 'journals/journal_confirm_archive.html', context)

@login_required
def journal_unarchive(request, pk):
    """View for unarchiving a journal"""
    journal = get_object_or_404(Journal, pk=pk, user=request.user)
    
    if request.method == 'POST':
        journal.is_archived = False
        journal.save(update_fields=['is_archived'])
        
        messages.success(request, f"Journal '{journal.title}' unarchived successfully!")
        return redirect('journals:detail', pk=journal.pk)
    
    context = {
        'journal': journal,
    }
    
    return render(request, 'journals/journal_confirm_unarchive.html', context)

@login_required
def journal_delete(request, pk):
    """View for deleting a journal"""
    journal = get_object_or_404(Journal, pk=pk, user=request.user)
    
    if request.method == 'POST':
        title = journal.title
        journal.delete()
        
        messages.success(request, f"Journal '{title}' deleted successfully!")
        return redirect('journals:list')
    
    context = {
        'journal': journal,
    }
    
    return render(request, 'journals/journal_confirm_delete.html', context)

@login_required
def entry_create(request, journal_pk):
    """View for creating a new journal entry"""
    journal = get_object_or_404(Journal, pk=journal_pk, user=request.user)
    
    if request.method == 'POST':
        form = JournalEntryForm(request.POST)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.journal = journal
            entry.save()
            
            # Save many-to-many relationships
            form.save_m2m()
            
            # Update journal's updated_at timestamp
            journal.updated_at = timezone.now()
            journal.save(update_fields=['updated_at'])
            
            messages.success(request, "Journal entry created successfully!")
            return redirect('journals:entry_detail', journal_pk=journal.pk, entry_pk=entry.pk)
    else:
        form = JournalEntryForm(initial={'entry_date': timezone.now().date()})
        
        # Check for a template ID in the query parameters
        template_id = request.GET.get('template')
        if template_id:
            try:
                template = JournalTemplate.objects.get(
                    Q(pk=template_id, user=request.user) | Q(pk=template_id, is_system=True)
                )
                form.fields['content'].initial = template.content
                form.fields['title'].initial = f"{template.title} - {timezone.now().strftime('%Y-%m-%d')}"
            except JournalTemplate.DoesNotExist:
                pass
        
        # Check for a prompt ID in the query parameters
        prompt_id = request.GET.get('prompt')
        if prompt_id:
            try:
                prompt = JournalPrompt.objects.get(
                    Q(pk=prompt_id, user=request.user) | Q(pk=prompt_id, is_system=True)
                )
                form.fields['content'].initial = f"Prompt: {prompt.text}\n\n"
                form.fields['title'].initial = f"Response to Prompt - {timezone.now().strftime('%Y-%m-%d')}"
            except JournalPrompt.DoesNotExist:
                pass
    
    # Get available characters for the form
    available_characters = Character.objects.filter(
        user=request.user,
        is_archived=False
    )
    
    # Get available templates
    templates = JournalTemplate.objects.filter(
        Q(user=request.user) | Q(is_system=True)
    ).order_by('title')
    
    # Get random prompts for inspiration
    random_prompts = JournalPrompt.objects.filter(
        Q(user=request.user) | Q(is_system=True)
    ).order_by('?')[:3]
    
    context = {
        'form': form,
        'journal': journal,
        'available_characters': available_characters,
        'templates': templates,
        'random_prompts': random_prompts,
    }
    
    return render(request, 'journals/entry_form.html', context)

@login_required
def entry_detail(request, journal_pk, entry_pk):
    """View for displaying a journal entry"""
    journal = get_object_or_404(Journal, pk=journal_pk, user=request.user)
    entry = get_object_or_404(JournalEntry, pk=entry_pk, journal=journal)
    
    # Get next and previous entries for navigation
    next_entry = JournalEntry.objects.filter(
        journal=journal,
        entry_date__gt=entry.entry_date
    ).order_by('entry_date', 'created_at').first()
    
    prev_entry = JournalEntry.objects.filter(
        journal=journal,
        entry_date__lt=entry.entry_date
    ).order_by('-entry_date', '-created_at').first()
    
    context = {
        'journal': journal,
        'entry': entry,
        'next_entry': next_entry,
        'prev_entry': prev_entry,
    }
    
    return render(request, 'journals/entry_detail.html', context)

@login_required
def entry_edit(request, journal_pk, entry_pk):
    """View for editing a journal entry"""
    journal = get_object_or_404(Journal, pk=journal_pk, user=request.user)
    entry = get_object_or_404(JournalEntry, pk=entry_pk, journal=journal)
    
    if request.method == 'POST':
        form = JournalEntryForm(request.POST, instance=entry)
        if form.is_valid():
            form.save()
            
            # Update journal's updated_at timestamp
            journal.updated_at = timezone.now()
            journal.save(update_fields=['updated_at'])
            
            messages.success(request, "Journal entry updated successfully!")
            return redirect('journals:entry_detail', journal_pk=journal.pk, entry_pk=entry.pk)
    else:
        form = JournalEntryForm(instance=entry)
    
    # Get available characters for the form
    available_characters = Character.objects.filter(
        user=request.user,
        is_archived=False
    )
    
    context = {
        'form': form,
        'journal': journal,
        'entry': entry,
        'available_characters': available_characters,
    }
    
    return render(request, 'journals/entry_form.html', context)

@login_required
def entry_delete(request, journal_pk, entry_pk):
    """View for deleting a journal entry"""
    journal = get_object_or_404(Journal, pk=journal_pk, user=request.user)
    entry = get_object_or_404(JournalEntry, pk=entry_pk, journal=journal)
    
    if request.method == 'POST':
        entry.delete()
        
        # Update journal's updated_at timestamp
        journal.updated_at = timezone.now()
        journal.save(update_fields=['updated_at'])
        
        messages.success(request, "Journal entry deleted successfully!")
        return redirect('journals:detail', pk=journal.pk)
    
    context = {
        'journal': journal,
        'entry': entry,
    }
    
    return render(request, 'journals/entry_confirm_delete.html', context)

@login_required
def template_list(request):
    """View for listing journal templates"""
    # Get user templates
    user_templates = JournalTemplate.objects.filter(user=request.user).order_by('title')
    
    # Get system templates
    system_templates = JournalTemplate.objects.filter(is_system=True).order_by('title')
    
    context = {
        'user_templates': user_templates,
        'system_templates': system_templates,
    }
    
    return render(request, 'journals/template_list.html', context)

@login_required
def template_create(request):
    """View for creating a new journal template"""
    if request.method == 'POST':
        form = JournalTemplateForm(request.POST)
        if form.is_valid():
            template = form.save(commit=False)
            template.user = request.user
            template.save()
            
            messages.success(request, f"Template '{template.title}' created successfully!")
            return redirect('journals:template_list')
    else:
        form = JournalTemplateForm()
    
    context = {
        'form': form,
        'is_new': True,
    }
    
    return render(request, 'journals/template_form.html', context)

@login_required
def template_edit(request, pk):
    """View for editing a journal template"""
    template = get_object_or_404(JournalTemplate, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = JournalTemplateForm(request.POST, instance=template)
        if form.is_valid():
            form.save()
            messages.success(request, f"Template '{template.title}' updated successfully!")
            return redirect('journals:template_list')
    else:
        form = JournalTemplateForm(instance=template)
    
    context = {
        'form': form,
        'template': template,
        'is_new': False,
    }
    
    return render(request, 'journals/template_form.html', context)

@login_required
def template_delete(request, pk):
    """View for deleting a journal template"""
    template = get_object_or_404(JournalTemplate, pk=pk, user=request.user)
    
    if request.method == 'POST':
        title = template.title
        template.delete()
        
        messages.success(request, f"Template '{title}' deleted successfully!")
        return redirect('journals:template_list')
    
    context = {
        'template': template,
    }
    
    return render(request, 'journals/template_confirm_delete.html', context)

@login_required
def prompt_list(request):
    """View for listing journal prompts"""
    # Get user prompts
    user_prompts = JournalPrompt.objects.filter(user=request.user).order_by('-created_at')
    
    # Get system prompts
    system_prompts = JournalPrompt.objects.filter(is_system=True).order_by('category', '?')
    
    # Get filter parameters
    category = request.GET.get('category')
    
    # Apply filters
    if category:
        system_prompts = system_prompts.filter(category=category)
    
    # Get all categories for the filter
    categories = JournalPrompt.PROMPT_CATEGORIES
    
    context = {
        'user_prompts': user_prompts,
        'system_prompts': system_prompts,
        'categories': categories,
        'filter_category': category,
    }
    
    return render(request, 'journals/prompt_list.html', context)

@login_required
def prompt_create(request):
    """View for creating a new journal prompt"""
    if request.method == 'POST':
        form = JournalPromptForm(request.POST)
        if form.is_valid():
            prompt = form.save(commit=False)
            prompt.user = request.user
            prompt.is_system = False
            prompt.save()
            
            messages.success(request, "Journal prompt created successfully!")
            return redirect('journals:prompt_list')
    else:
        form = JournalPromptForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'journals/prompt_form.html', context)

@login_required
def prompt_delete(request, pk):
    """View for deleting a journal prompt"""
    prompt = get_object_or_404(JournalPrompt, pk=pk, user=request.user)
    
    if request.method == 'POST':
        prompt.delete()
        
        messages.success(request, "Journal prompt deleted successfully!")
        return redirect('journals:prompt_list')
    
    context = {
        'prompt': prompt,
    }
    
    return render(request, 'journals/prompt_confirm_delete.html', context)

@login_required
def random_prompt(request):
    """API view for getting a random journal prompt"""
    category = request.GET.get('category')
    
    # Base queryset for prompts
    prompts = JournalPrompt.objects.filter(
        Q(user=request.user) | Q(is_system=True)
    )
    
    # Apply category filter if provided
    if category:
        prompts = prompts.filter(category=category)
    
    # Get a random prompt
    count = prompts.count()
    if count > 0:
        random_index = random.randint(0, count - 1)
        prompt = prompts[random_index]
        
        return JsonResponse({
            'id': prompt.id,
            'text': prompt.text,
            'category': prompt.category
        })
    else:
        return JsonResponse({
            'error': 'No prompts found'
        }, status=404)
    