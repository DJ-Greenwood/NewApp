import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.db.models import Count

from .models import Character, CharacterMemory, CharacterRelationship
from .forms import CharacterForm, CharacterGenerationForm
from core.services.openai_service import OpenAIService
from core.services.pinecone_service import PineconeService
from token_management.models import UserTokenLimit

@login_required
def character_list(request):
    """View for listing all characters belonging to the user"""
    characters = Character.objects.filter(
        user=request.user,
        is_archived=False
    ).order_by('-last_interaction', '-created_at')
    
    archived_characters = []
    if request.GET.get('show_archived'):
        archived_characters = Character.objects.filter(
            user=request.user,
            is_archived=True
        ).order_by('-last_interaction', '-created_at')
    
    # Get characters with most interactions
    favorite_characters = Character.objects.filter(
        user=request.user,
        is_archived=False,
        total_interactions__gt=0
    ).order_by('-total_interactions')[:5]
    
    # Get recently active characters
    recent_characters = Character.objects.filter(
        user=request.user,
        is_archived=False,
        last_interaction__isnull=False
    ).order_by('-last_interaction')[:5]
    
    context = {
        'characters': characters,
        'archived_characters': archived_characters,
        'favorite_characters': favorite_characters,
        'recent_characters': recent_characters,
    }
    
    return render(request, 'pages/characters/character_list.html', context)

@login_required
def character_detail(request, pk):
    """View for displaying character details"""
    character = get_object_or_404(Character, pk=pk, user=request.user)
    
    # Get character memories
    memories = CharacterMemory.objects.filter(
        character=character,
        is_active=True
    ).order_by('-importance_score')[:10]
    
    # Get character relationships
    relationships = CharacterRelationship.objects.filter(
        character=character
    ).select_related('related_character')
    
    # Get conversations with this character
    conversations = character.conversations.filter(
        is_archived=False
    ).order_by('-updated_at')[:5]
    
    context = {
        'character': character,
        'memories': memories,
        'relationships': relationships,
        'conversations': conversations,
    }
    
    return render(request, 'pages/characters/character_detail.html', context)

@login_required
def character_create(request):
    """View for manually creating a new character"""
    # Check if user has reached their character limit
    character_limit = get_character_limit(request.user)
    current_count = Character.objects.filter(
        user=request.user,
        is_archived=False
    ).count()
    
    if current_count >= character_limit:
        messages.error(
            request, 
            f"You have reached your limit of {character_limit} characters. "
            f"Please upgrade your subscription or archive existing characters."
        )
        return redirect('characters:list')
    
    # Process form
    if request.method == 'POST':
        form = CharacterForm(request.POST, request.FILES)
        if form.is_valid():
            character = form.save(commit=False)
            character.user = request.user
            character.save()
            
            # Create vector embedding
            try:
                pinecone_service = PineconeService()
                vector_id = pinecone_service.store_character_embedding(character)
                
                # Save the vector ID
                character.vector_id = vector_id
                character.save(update_fields=['vector_id'])
                
                messages.success(request, f"Character '{character.name}' was successfully created!")
            except Exception as e:
                # Log the error but don't prevent character creation
                print(f"Error creating vector embedding: {str(e)}")
                messages.warning(
                    request, 
                    f"Character created, but there was an issue with the vector embedding. Some features may be limited."
                )
            
            return redirect('characters:detail', pk=character.pk)
    else:
        form = CharacterForm()
        
        # Check if there's a prompt in the query parameters
        prompt = request.GET.get('prompt')
        if prompt:
            form.fields['description'].initial = prompt
    
    context = {
        'form': form,
        'character_limit': character_limit,
        'current_count': current_count,
        'is_new': True,
    }
    
    return render(request, 'pages/characters/character_form.html', context)

@login_required
def character_edit(request, pk):
    """View for editing an existing character"""
    character = get_object_or_404(Character, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = CharacterForm(request.POST, request.FILES, instance=character)
        if form.is_valid():
            updated_character = form.save()
            
            # Update vector embedding
            try:
                pinecone_service = PineconeService()
                vector_id = pinecone_service.store_character_embedding(updated_character)
                
                # Save the vector ID if it changed
                if vector_id != updated_character.vector_id:
                    updated_character.vector_id = vector_id
                    updated_character.save(update_fields=['vector_id'])
                
                messages.success(request, f"Character '{updated_character.name}' was successfully updated!")
            except Exception as e:
                # Log the error but don't prevent character update
                print(f"Error updating vector embedding: {str(e)}")
                messages.warning(
                    request, 
                    f"Character updated, but there was an issue with the vector embedding. Some features may be limited."
                )
            
            return redirect('characters:detail', pk=updated_character.pk)
    else:
        # Initialize form with traits converted to comma-separated string
        traits_string = ', '.join(character.get_traits_list())
        
        form = CharacterForm(instance=character, initial={'traits_input': traits_string})
    
    context = {
        'form': form,
        'character': character,
        'is_new': False,
    }
    
    return render(request, 'pages/characters/character_form.html', context)

@login_required
def character_delete(request, pk):
    """View for deleting a character"""
    character = get_object_or_404(Character, pk=pk, user=request.user)
    
    if request.method == 'POST':
        # Delete the character's vector embeddings
        try:
            pinecone_service = PineconeService()
            pinecone_service.delete_character_vectors(character)
        except Exception as e:
            # Log the error but continue with deletion
            print(f"Error deleting vector embeddings: {str(e)}")
        
        character_name = character.name
        character.delete()
        
        messages.success(request, f"Character '{character_name}' was successfully deleted!")
        return redirect('characters:list')
    
    context = {
        'character': character,
    }
    
    return render(request, 'pages/characters/character_confirm_delete.html', context)

@login_required
def character_archive(request, pk):
    """View for archiving a character"""
    character = get_object_or_404(Character, pk=pk, user=request.user)
    
    if request.method == 'POST':
        character.is_archived = True
        character.save(update_fields=['is_archived'])
        
        messages.success(request, f"Character '{character.name}' was archived.")
        return redirect('characters:list')
    
    context = {
        'character': character,
    }
    
    return render(request, 'pages/characters/character_confirm_archive.html', context)

@login_required
def character_unarchive(request, pk):
    """View for unarchiving a character"""
    character = get_object_or_404(Character, pk=pk, user=request.user)
    
    # Check if user has reached their character limit
    character_limit = get_character_limit(request.user)
    current_count = Character.objects.filter(
        user=request.user,
        is_archived=False
    ).count()
    
    if current_count >= character_limit:
        messages.error(
            request, 
            f"You have reached your limit of {character_limit} characters. "
            f"Please upgrade your subscription or archive existing characters before unarchiving."
        )
        return redirect('characters:list')
    
    if request.method == 'POST':
        character.is_archived = False
        character.save(update_fields=['is_archived'])
        
        messages.success(request, f"Character '{character.name}' was unarchived.")
        return redirect('characters:detail', pk=character.pk)
    
    context = {
        'character': character,
    }
    
    return render(request, 'pages/characters/character_confirm_unarchive.html', context)

@login_required
def character_generate(request):
    """View for AI-assisted character generation"""
    # Check if user has reached their character limit
    character_limit = get_character_limit(request.user)
    current_count = Character.objects.filter(
        user=request.user,
        is_archived=False
    ).count()
    
    if current_count >= character_limit:
        messages.error(
            request, 
            f"You have reached your limit of {character_limit} characters. "
            f"Please upgrade your subscription or archive existing characters."
        )
        return redirect('characters:list')
    
    # Check if user has enough tokens - UPDATED
    try:
        token_limit_obj = UserTokenLimit.objects.get(user=request.user)
        if token_limit_obj.current_usage >= token_limit_obj.monthly_limit:
            messages.error(
                request,
                "You have reached your monthly token limit. "
                "Please upgrade your subscription or purchase additional tokens."
            )
            return redirect('token_management:limit_reached')
    except UserTokenLimit.DoesNotExist:
        # Create default token limit if it doesn't exist
        token_limit_obj = UserTokenLimit.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = CharacterGenerationForm(request.POST)
        if form.is_valid():
            # Get form data
            name = form.cleaned_data['name']
            concept = form.cleaned_data['concept']
            traits = form.cleaned_data['traits']
            additional_info = form.cleaned_data['additional_info']
            
            # Generate character using OpenAI
            try:
                openai_service = OpenAIService(request.user)
                result = openai_service.create_character(
                    name=name,
                    description=f"{concept}\n{additional_info if additional_info else ''}",
                    traits=traits
                )
                
                # Create character from generated data
                character_data = result['character_data']
                token_usage = result['token_usage']
                
                # Create new character
                character = Character(
                    user=request.user,
                    name=name,
                    description=concept,
                    background_story=character_data.get('background_story', ''),
                    personality_details=character_data.get('personality', {}),
                    voice=character_data.get('voice', ''),
                    traits=character_data.get('personality', {}).get('core_traits', []),
                    creation_token_cost=token_usage['total_tokens']
                )
                character.save()
                
                # Create vector embedding
                try:
                    pinecone_service = PineconeService()
                    vector_id = pinecone_service.store_character_embedding(character)
                    
                    # Save the vector ID
                    character.vector_id = vector_id
                    character.save(update_fields=['vector_id'])
                except Exception as e:
                    # Log the error but don't prevent character creation
                    print(f"Error creating vector embedding: {str(e)}")
                
                messages.success(request, f"Character '{character.name}' was successfully generated!")
                return redirect('characters:detail', pk=character.pk)
                
            except Exception as e:
                # Log the error and show message
                print(f"Error generating character: {str(e)}")
                messages.error(
                    request,
                    "There was an error generating your character. Please try again."
                )
    else:
        form = CharacterGenerationForm()
        
        # Check if there's a prompt in the query parameters
        prompt = request.GET.get('prompt')
        if prompt:
            form.fields['concept'].initial = prompt
    
    context = {
        'form': form,
        'character_limit': character_limit,
        'current_count': current_count,
    }
    
    return render(request, 'pages/characters/character_generate.html', context)

@login_required
def add_character_memory(request, pk):
    """Add a new memory to a character"""
    character = get_object_or_404(Character, pk=pk, user=request.user)
    
    if request.method == 'POST':
        content = request.POST.get('memory_content')
        importance = float(request.POST.get('importance', 0.5))
        source = request.POST.get('source', 'manual')
        
        if content:
            # Create the memory
            memory = CharacterMemory.objects.create(
                character=character,
                content=content,
                importance_score=importance,
                source=source
            )
            
            # Create vector embedding
            try:
                pinecone_service = PineconeService()
                vector_id = pinecone_service.store_memory_embedding(memory)
                
                # Save the vector ID
                memory.vector_id = vector_id
                memory.save(update_fields=['vector_id'])
            except Exception as e:
                # Log the error but don't prevent memory creation
                print(f"Error creating memory embedding: {str(e)}")
            
            messages.success(request, "Memory added successfully!")
        else:
            messages.error(request, "Memory content cannot be empty.")
        
        return redirect('characters:detail', pk=character.pk)
    
    # If not POST, redirect to character detail
    return redirect('characters:detail', pk=character.pk)

def get_character_limit(user):
    """Helper function to get character limit based on subscription tier"""
    tier_limits = {
        'free': 3,
        'basic': 10,
        'enterprise': 999999,  # effectively unlimited
    }
    
    return tier_limits.get(user.subscription_tier, 3)