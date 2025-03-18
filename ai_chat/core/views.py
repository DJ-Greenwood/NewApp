import random
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from characters.models import Character
from conversations.models import Conversation, Message
from stories.models import Story
from journals.models import Journal
from token_management.context_processors import token_usage

def home(request):
    """Home page view"""
    # If user is authenticated, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    return render(request, 'home.html')

@login_required
def dashboard(request):
    """Dashboard view for authenticated users"""
    user = request.user
    
    # Get recent characters
    recent_characters = Character.objects.filter(
        user=user,
        is_archived=False
    ).order_by('-last_interaction', '-created_at')[:5]
    
    # Get recent activity (combine conversations, characters, stories, journals)
    recent_activity = []
    
    # Add recent conversations
    conversations = Conversation.objects.filter(
        user=user,
        is_archived=False
    ).order_by('-updated_at')[:5]
    
    for conv in conversations:
        recent_activity.append({
            'type': 'conversation',
            'title': f'Conversation with {conv.character.name}',
            'timestamp': conv.updated_at,
            'tokens': conv.total_tokens,
            'description': get_latest_message_content(conv),
            'url': f'/conversations/{conv.id}/'
        })
    
    # Add recently created characters
    new_characters = Character.objects.filter(
        user=user,
        is_archived=False
    ).order_by('-created_at')[:3]
    
    for char in new_characters:
        # Avoid duplicating characters in the activity feed if they're in recent characters
        if not any(a.get('type') == 'character' and char.name in a.get('title') for a in recent_activity):
            recent_activity.append({
                'type': 'character',
                'title': f'Created {char.name}',
                'timestamp': char.created_at,
                'tokens': char.creation_token_cost,
                'description': char.description[:100] if char.description else None,
                'url': f'/characters/{char.id}/'
            })
    
    # Add recent stories
    stories = Story.objects.filter(
        user=user
    ).order_by('-updated_at')[:3]
    
    for story in stories:
        recent_activity.append({
            'type': 'story',
            'title': story.title,
            'timestamp': story.updated_at,
            'tokens': getattr(story, 'token_usage', 0) or 0,
            'description': story.description[:100] if story.description else None,
            'url': f'/stories/{story.id}/'
        })
    
    # Add recent journals
    journals = Journal.objects.filter(
        user=user
    ).order_by('-updated_at')[:3]
    
    for journal in journals:
        recent_activity.append({
            'type': 'journal',
            'title': journal.title,
            'timestamp': journal.updated_at,
            'tokens': 0,  # Journals don't use tokens directly
            'description': journal.description[:100] if journal.description else None,
            'url': f'/journals/{journal.id}/'
        })
    
    # Sort by timestamp and take the 10 most recent
    recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activity = recent_activity[:10]
    
    # Generate inspiration prompts
    inspiration = get_inspiration_prompts()
    
    # Calculate days until token reset
    token_reset_date = user.token_reset_date
    today = timezone.now().date()
    if token_reset_date and token_reset_date.month == today.month and token_reset_date.year == today.year:
        # Same month, calculate next month
        next_month = today.replace(day=28) + timezone.timedelta(days=4)
        next_reset = next_month.replace(day=1)
    else:
        # Already have a reset date or token_reset_date is None
        next_reset = token_reset_date if token_reset_date else today.replace(day=1, month=today.month + 1)
    
    days_until_reset = (next_reset - today).days
    
    # Get token usage information from user or profile
    token_usage = getattr(user, 'token_usage', 0)
    token_limit = getattr(user, 'token_limit', 50000)  # Default to free tier limit
    # Extract numeric values if these are model instances
    if hasattr(token_usage, 'value'):
        token_usage = token_usage.value
    elif not isinstance(token_usage, (int, float)):
        token_usage = 0

    if hasattr(token_limit, 'value'):
        token_limit = token_limit.value
    elif not isinstance(token_limit, (int, float)):
        token_limit = 50000  # Default to free tier

    token_percent = (token_usage / token_limit * 100) if token_limit > 0 else 0
    
    context = {
        'recent_characters': recent_characters,
        'recent_activity': recent_activity,
        'inspiration': inspiration,
        'days_until_reset': days_until_reset,
        'token_usage': token_usage,
        'token_limit': token_limit,
        'token_percent': token_percent,
    }
    
    return render(request, 'pages/dashboard.html', context)

def get_latest_message_content(conversation):
    """Helper function to get the latest message in a conversation"""
    latest_message = Message.objects.filter(
        conversation=conversation
    ).order_by('-timestamp').first()
    
    if latest_message:
        # Truncate message content
        content = latest_message.content
        sender = 'You' if latest_message.sender == 'user' else conversation.character.name
        return f"{sender}: {content}"
    
    return None

def get_inspiration_prompts():
    """Generate random inspiration prompts for the dashboard"""
    character_ideas = [
        "A detective who can speak to inanimate objects at crime scenes",
        "A time-traveling historian trying to fix anachronisms",
        "A retired superhero adjusting to normal life",
        "A robot developing consciousness and emotions",
        "A barista who can read customers' futures in their coffee",
        "A ghost who doesn't know they're dead",
        "A librarian who can enter the worlds of books",
        "A geneticist who accidentally gave themselves animal abilities",
        "An immortal trying to find meaning in endless existence",
        "A dream archaeologist who explores forgotten memories"
    ]
    
    conversation_starters = [
        "What's the most beautiful place you've ever visited?",
        "If you could change one moment in history, what would it be?",
        "What's your philosophy on what makes a good life?",
        "Tell me about your greatest adventure.",
        "What do you think happens after we die?",
        "If you could have dinner with anyone, living or dead, who would it be?",
        "What would you do if you knew you couldn't fail?",
        "What's your greatest fear, and how do you face it?",
        "Tell me about a time when you had to be brave.",
        "What would your perfect day look like?"
    ]
    
    story_ideas = [
        "A hidden door in an old house leads to a parallel world",
        "Someone discovers they can hear everyone's inner thoughts",
        "A forgotten AI awakens in an abandoned space station",
        "A character receives letters from their future self",
        "A small town where nobody can tell a lie for one day",
        "Two enemies are forced to work together to survive",
        "Someone discovers they're a character in a novel",
        "A world where dreams physically manifest while people sleep",
        "A mysterious object grants unpredictable wishes",
        "A journey to return a lost item to its original owner"
    ]
    
    return {
        'character_idea': random.choice(character_ideas),
        'conversation_starter': random.choice(conversation_starters),
        'story_idea': random.choice(story_ideas)
    }

def token_usage(request):
    """View to display token usage information"""
    user = request.user
    token_usage = token_usage(request)['token_usage']
    token_limit = request(request)['token_limit']

    context = {
        'token_usage': token_usage,
        'token_limit': token_limit,
    }
    
    return render(request, 'alerts/token_usage.html', context)  # Adjust template path as needed