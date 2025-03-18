from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.db.models import Count, Prefetch

from .models import Conversation, Message, ConversationSummary
from characters.models import Character, CharacterMemory
from core.services.openai_service import OpenAIService
from core.services.pinecone_service import PineconeService
import json


@login_required
def conversation_list(request):
    """View for listing all conversations"""
    # Get filter parameters
    character_id = request.GET.get('character')
    show_archived = request.GET.get('show_archived') == '1'
    
    # Base queryset
    conversations = Conversation.objects.filter(user=request.user)
    
    # Apply filters
    if character_id:
        conversations = conversations.filter(character_id=character_id)
    
    if not show_archived:
        conversations = conversations.filter(is_archived=False)
    
    # Add prefetch for optimization
    conversations = conversations.select_related('character').prefetch_related(
        Prefetch('messages', queryset=Message.objects.order_by('-timestamp')[:1])
    )
    
    # Get conversation statistics
    total_conversations = conversations.count()
    total_messages = Message.objects.filter(conversation__user=request.user).count()
    total_tokens = sum(c.total_tokens for c in conversations)
    
    # Get characters with conversations
    characters_with_convos = Character.objects.filter(
        conversations__user=request.user
    ).distinct().order_by('name')
    
    context = {
        'conversations': conversations,
        'total_conversations': total_conversations,
        'total_messages': total_messages,
        'total_tokens': total_tokens,
        'characters': characters_with_convos,
        'filter_character_id': character_id,
        'show_archived': show_archived,
    }
    
    return render(request, 'pages/conversations/conversation.html', context)

@login_required
def conversation_detail(request, pk):
    """View for displaying a conversation"""
    conversation = get_object_or_404(Conversation, pk=pk, user=request.user)
    character = conversation.character
    
    # Get messages
    messages = Message.objects.filter(conversation=conversation).order_by('timestamp')
    
    # Mark unread messages as read
    conversation.mark_as_read()
    
    # If this is a POST request, add a new message
    if request.method == 'POST':
        user_message = request.POST.get('message')
        
        if user_message:
            # Create user message
            Message.objects.create(
                conversation=conversation,
                content=user_message,
                sender='user',
                is_read=True  # User's own messages are always read
            )
            
            # Generate character response
            try:
                # Get conversation history for context
                message_history = messages.order_by('-timestamp')[:10]  # Last 10 messages for context
                message_history = reversed(list(message_history))  # Put in chronological order
                
                # Create OpenAI service
                openai_service = OpenAIService(request.user)
                
                # Generate response
                response = openai_service.generate_character_response(
                    character=character,
                    conversation_history=message_history,
                    user_message=user_message
                )
                
                # Create character message
                Message.objects.create(
                    conversation=conversation,
                    content=response['response'],
                    sender='character',
                    prompt_tokens=response['token_usage']['prompt_tokens'],
                    completion_tokens=response['token_usage']['completion_tokens'],
                    is_read=True  # Mark as read since user is currently viewing
                )
                
                # Update conversation's total tokens
                conversation.add_tokens(response['token_usage']['total_tokens'])
                
                # Update character's last interaction timestamp
                character.last_interaction = timezone.now()
                character.save(update_fields=['last_interaction'])
                
                # Check if we should create a memory from this interaction
                if len(user_message) > 50:  # Only create memories from substantial messages
                    try:
                        create_memory_from_message(character, user_message)
                    except Exception as e:
                        # Log error but don't interrupt the conversation flow
                        print(f"Error creating memory: {str(e)}")
                
                messages.success(request, "Message sent successfully!")
            except Exception as e:
                messages.error(request, f"Error generating response: {str(e)}")
            
            # Redirect to refresh the page and avoid form resubmission
            return redirect('conversations:detail', pk=conversation.pk)
    
    # Get other recent conversations with this character
    other_conversations = Conversation.objects.filter(
        user=request.user,
        character=character,
        is_archived=False
    ).exclude(pk=conversation.pk).order_by('-updated_at')[:5]
    
    context = {
        'conversation': conversation,
        'character': character,
        'messages': messages,
        'other_conversations': other_conversations,
    }
    
    return render(request, 'pages/conversations/conversation_detail.html', context)

@login_required
def conversation_create(request):
    """View for creating a new conversation"""
    # Get available characters
    characters = Character.objects.filter(
        user=request.user,
        is_archived=False
    ).order_by('-last_interaction', '-created_at')
    
    if request.method == 'POST':
        character_id = request.POST.get('character_id')
        context = request.POST.get('context', '')
        
        if character_id:
            character = get_object_or_404(Character, pk=character_id, user=request.user)
            
            # Create new conversation
            conversation = Conversation.objects.create(
                user=request.user,
                character=character,
                title=f"Conversation with {character.name}",
                context=context
            )
            
            # Add system message with context if provided
            if context:
                Message.objects.create(
                    conversation=conversation,
                    content=f"Context: {context}",
                    sender='system'
                )
            
            messages.success(request, f"Started a new conversation with {character.name}!")
            return redirect('conversations:detail', pk=conversation.pk)
        else:
            messages.error(request, "Please select a character to start a conversation.")
    
    # Check for a prompt in the query parameters
    initial_prompt = request.GET.get('prompt', '')
    
    context = {
        'characters': characters,
        'initial_prompt': initial_prompt,
    }
    
    return render(request, 'pages/conversations/conversation_create.html', context)

@login_required
def conversation_create_with_character(request, character_id):
    """View for creating a new conversation with a specific character"""
    character = get_object_or_404(Character, pk=character_id, user=request.user)
    
    # Create new conversation
    conversation = Conversation.objects.create(
        user=request.user,
        character=character,
        title=f"Conversation with {character.name}"
    )
    
    messages.success(request, f"Started a new conversation with {character.name}!")
    return redirect('conversations:detail', pk=conversation.pk)

@login_required
def conversation_archive(request, pk):
    """View for archiving a conversation"""
    conversation = get_object_or_404(Conversation, pk=pk, user=request.user)
    
    if request.method == 'POST':
        conversation.is_archived = True
        conversation.save(update_fields=['is_archived'])
        
        messages.success(request, "Conversation archived successfully!")
        return redirect('conversations:list')
    
    context = {
        'conversation': conversation,
    }
    
    return render(request, 'pages/conversations/conversation_confirm_archive.html', context)

@login_required
def conversation_unarchive(request, pk):
    """View for unarchiving a conversation"""
    conversation = get_object_or_404(Conversation, pk=pk, user=request.user)
    
    if request.method == 'POST':
        conversation.is_archived = False
        conversation.save(update_fields=['is_archived'])
        
        messages.success(request, "Conversation unarchived successfully!")
        return redirect('conversations:detail', pk=conversation.pk)
    
    context = {
        'conversation': conversation,
    }
    
    return render(request, 'pages/conversations/conversation_confirm_unarchive.html', context)

@login_required
def conversation_delete(request, pk):
    """View for deleting a conversation"""
    conversation = get_object_or_404(Conversation, pk=pk, user=request.user)
    
    if request.method == 'POST':
        character_id = conversation.character.id
        conversation.delete()
        
        messages.success(request, "Conversation deleted successfully!")
        return redirect('conversations:list')
    
    context = {
        'conversation': conversation,
    }
    
    return render(request, 'pages/conversations/conversation_confirm_delete.html', context)

@login_required
def create_summary(request, pk):
    """View for creating a conversation summary"""
    conversation = get_object_or_404(Conversation, pk=pk, user=request.user)
    
    if request.method == 'POST':
        # Get message range to summarize
        start_id = request.POST.get('start_message_id')
        end_id = request.POST.get('end_message_id')
        
        if start_id and end_id:
            try:
                # Get messages to summarize
                start_message = get_object_or_404(Message, pk=start_id, conversation=conversation)
                end_message = get_object_or_404(Message, pk=end_id, conversation=conversation)
                
                # Ensure end message comes after start message
                if end_message.timestamp < start_message.timestamp:
                    start_message, end_message = end_message, start_message
                
                # Get all messages in range
                messages_to_summarize = Message.objects.filter(
                    conversation=conversation,
                    timestamp__gte=start_message.timestamp,
                    timestamp__lte=end_message.timestamp
                ).order_by('timestamp')
                
                # Create OpenAI service
                openai_service = OpenAIService(request.user)
                
                # Generate summary
                result = openai_service.summarize_conversation(
                    conversation=conversation,
                    messages=messages_to_summarize
                )
                
                # Create summary
                summary = ConversationSummary.objects.create(
                    conversation=conversation,
                    content=result['summary'],
                    start_message=start_message,
                    end_message=end_message,
                    token_count=result['token_usage']['total_tokens']
                )
                
                # Update conversation's total tokens
                conversation.add_tokens(result['token_usage']['total_tokens'])
                
                messages.success(request, "Conversation segment summarized successfully!")
            except Exception as e:
                messages.error(request, f"Error creating summary: {str(e)}")
        else:
            messages.error(request, "Please select a valid message range to summarize.")
    
    return redirect('conversations:detail', pk=conversation.pk)

def create_memory_from_message(character, message_content):
    """Helper function to create a memory from a message"""
    # Create memory
    memory = CharacterMemory.objects.create(
        character=character,
        content=message_content,
        importance_score=0.5,  # Default importance
        source='conversation'
    )
    
    # Create vector embedding
    try:
        pinecone_service = PineconeService()
        vector_id = pinecone_service.store_memory_embedding(memory)
        
        # Save the vector ID
        memory.vector_id = vector_id
        memory.save(update_fields=['vector_id'])
    except Exception as e:
        # Log error but don't fail memory creation
        print(f"Error creating memory embedding: {str(e)}")
    
    return memory

@login_required
def conversation_list(request):
    """View for listing all conversations"""
    # Get filter parameters
    character_id = request.GET.get('character')
    show_archived = request.GET.get('show_archived') == '1'
    
    # Base queryset
    conversations = Conversation.objects.filter(user=request.user)
    
    # Apply filters
    if character_id:
        conversations = conversations.filter(character_id=character_id)
    
    if not show_archived:
        conversations = conversations.filter(is_archived=False)
    
    # Add prefetch for optimization - Fixed: don't try to filter after slicing
    conversations = conversations.select_related('character').prefetch_related(
        Prefetch('messages', queryset=Message.objects.order_by('-timestamp'), to_attr='recent_messages')
    )
    
    # Get conversation statistics
    total_conversations = conversations.count()
    total_messages = Message.objects.filter(conversation__user=request.user).count()
    
    # Calculate total tokens without using a sliced queryset
    total_tokens = sum(c.total_tokens for c in conversations)
    
    # Get characters with conversations
    characters_with_convos = Character.objects.filter(
        conversations__user=request.user
    ).distinct().order_by('name')
    
    context = {
        'conversations': conversations,
        'total_conversations': total_conversations,
        'total_messages': total_messages,
        'total_tokens': total_tokens,
        'characters': characters_with_convos,
        'filter_character_id': character_id,
        'show_archived': show_archived,
    }
    
    return render(request, 'pages/conversations/conversation_list.html', context)

@login_required
def send_message(request, pk):
    """API view for sending messages via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    conversation = get_object_or_404(Conversation, pk=pk, user=request.user)
    character = conversation.character
    
    try:
        data = json.loads(request.body)
        user_message = data.get('message', '')
        
        if not user_message:
            return JsonResponse({'error': 'Message content is required'}, status=400)
        
        # Create user message
        user_msg = Message.objects.create(
            conversation=conversation,
            content=user_message,
            sender='user',
            is_read=True
        )
        
        # Get conversation history for context
        messages_history = Message.objects.filter(conversation=conversation).order_by('-timestamp')[:10]
        messages_history = reversed(list(messages_history))
        
        # Create OpenAI service
        openai_service = OpenAIService(request.user)
        
        # Generate response
        response = openai_service.generate_character_response(
            character=character,
            conversation_history=messages_history,
            user_message=user_message
        )
        
        # Create character message
        char_msg = Message.objects.create(
            conversation=conversation,
            content=response['response'],
            sender='character',
            prompt_tokens=response['token_usage']['prompt_tokens'],
            completion_tokens=response['token_usage']['completion_tokens'],
            is_read=True
        )
        
        # Update conversation's total tokens
        conversation.add_tokens(response['token_usage']['total_tokens'])
        
        # Update character's last interaction timestamp
        character.last_interaction = timezone.now()
        character.save(update_fields=['last_interaction'])
        
        # Create memory if applicable
        if len(user_message) > 50:
            try:
                create_memory_from_message(character, user_message)
            except Exception as e:
                print(f"Error creating memory: {str(e)}")
        
        return JsonResponse({
            'message': response['response'],
            'timestamp': char_msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def toggle_favorite(request, conversation_id):
    """View for toggling a conversation as favorite"""
    conversation = get_object_or_404(Conversation, pk=conversation_id, user=request.user)
    
    # You'll need to add the is_favorite field to your Conversation model
    conversation.is_favorite = not conversation.is_favorite
    conversation.save(update_fields=['is_favorite'])
    
    messages.success(request, "Conversation favorite status updated!")
    
    # Redirect back to previous page
    return redirect(request.META.get('HTTP_REFERER', 'conversations:list'))

@login_required
def conversation_export(request, conversation_id):
    """View for exporting a conversation"""
    conversation = get_object_or_404(Conversation, pk=conversation_id, user=request.user)
    
    # Get all messages
    messages_list = Message.objects.filter(conversation=conversation).order_by('timestamp')
    
    # Build the export content
    export_content = f"Conversation with {conversation.character.name}\n"
    export_content += f"Started: {conversation.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
    
    for msg in messages_list:
        sender = "You" if msg.sender == 'user' else conversation.character.name
        export_content += f"{sender} ({msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}):\n{msg.content}\n\n"
    
    # Create the HTTP response with the file
    response = HttpResponse(export_content, content_type='text/plain')
    response['Content-Disposition'] = f'attachment; filename="conversation_with_{conversation.character.name}_{conversation.id}.txt"'
    
    return response

