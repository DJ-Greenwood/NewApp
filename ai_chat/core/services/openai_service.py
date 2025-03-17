import json
from openai import OpenAI
from django.conf import settings
from token_management.models import UserTokenLimit, TokenUsage

# Set OpenAI API key
client = OpenAI(api_key=settings.OPENAI_API_KEY)

class OpenAIService:
    """Service for interacting with OpenAI APIs"""
    
    def __init__(self, user):
        self.user = user

    def create_character(self, name, description, traits=None):
        """
        Create a new character using OpenAI
        Returns character details and token usage
        """
        system_prompt = """You are a creative assistant that helps create detailed fictional characters.
        Generate a rich character profile based on the given name, description, and traits.
        Provide a background story, personality traits, voice characteristics, and how they might 
        respond in various situations. Make the character feel well-rounded and authentic."""
        
        user_prompt = f"""
        Create a detailed character profile for:
        Name: {name}
        Description: {description}
        {"Traits: " + ", ".join(traits) if traits else ""}
        
        Please include:
        1. A rich background story
        2. Detailed personality traits
        3. Voice and speech patterns
        4. How they behave in different scenarios
        5. Core motivations and fears
        
        Format the response as JSON with the following structure:
        {{
            "background_story": "string",
            "personality": {{
                "core_traits": ["string", "string", ...],
                "strengths": ["string", "string", ...], 
                "weaknesses": ["string", "string", ...],
                "quirks": ["string", "string", ...]
            }},
            "voice": "string",
            "scenarios": {{
                "when_happy": "string",
                "when_sad": "string",
                "when_angry": "string",
                "when_stressed": "string"
            }},
            "motivations": ["string", "string", ...],
            "fears": ["string", "string", ...]
        }}
        """
        
        response = client.chat.completions.create(
            model="gpt-4",  # Using GPT-4 for higher quality characters
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2000,
        )
        
        # Log token usage - Fixed to use object properties instead of dictionary access
        token_usage = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }
        
        self._log_token_usage(
            feature='character_creation',
            tokens_used=token_usage['total_tokens'],
            character_id=None  # Will be updated after character creation
        )
        
        # Parse the response - Fixed to access response content properly
        character_content = response.choices[0].message.content
        try:
            character_data = json.loads(character_content)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract JSON from the text
            print(f'Error decoding JSON directly, attempting to extract JSON from text')
            import re
            json_match = re.search(r'({.*})', character_content.replace('\n', ' '), re.DOTALL)
            if json_match:
                try:
                    character_data = json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    print(f'Error extracting JSON: {character_content}')
                    character_data = {"error": "Failed to parse character data"}
            else:
                print(f'No JSON found in response: {character_content}')
                character_data = {"error": "Failed to parse character data"}
                    
        return {
            'character_data': character_data,
            'token_usage': token_usage,
        }
    
    def generate_character_response(self, character, conversation_history, user_message):
        """
        Generate a character's response to a user message
        Returns the response and token usage
        """
        # Create system prompt based on character details
        system_prompt = f"""You are roleplaying as {character.name}. Here are details about your character:
        
        Background: {character.background_story}
        
        Voice: {character.voice}
        
        Traits: {', '.join(character.get_traits_list())}
        
        Always stay in character and respond as {character.name} would. Never break character
        or acknowledge that you are an AI. Respond directly as the character would speak.
        """
        
        # Build messages from conversation history
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history
        for msg in conversation_history:
            role = "assistant" if msg.sender == "character" else "user"
            messages.append({"role": role, "content": msg.content})
        
        # Add the current user message
        messages.append({"role": "user", "content": user_message})
        
        # Get relevant memories
        memories = character.get_memory_objects()[:5]  # Limit to 5 most important memories
        if memories:
            memory_text = "Here are some relevant memories that might influence your response:\n\n"
            for memory in memories:
                memory_text += f"- {memory.content}\n"
                memory.access()  # Mark memory as accessed
            
            # Add memories as a separate system message
            messages.append({"role": "system", "content": memory_text})
        
        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Use a less expensive model for regular chat
            messages=messages,
            temperature=0.8,
            max_tokens=800
        )
        
        # Log token usage - Fixed to use object properties
        token_usage = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }
        
        self._log_token_usage(
            feature='character_chat',
            tokens_used=token_usage['total_tokens'],
            character_id=character.id,
            conversation_id=conversation_history[0].conversation.id if conversation_history else None
        )
        
        # Update character's interaction records
        character.record_interaction(token_usage['total_tokens'])
        
        return {
            'response': response.choices[0].message.content,
            'token_usage': token_usage,
        }
    
    def summarize_conversation(self, conversation, messages):
        """
        Summarize a conversation segment
        Returns the summary and token usage
        """
        system_prompt = """You are a helpful assistant that summarizes conversations.
        Create a concise summary that captures the key points, decisions, and important 
        information from the conversation. Focus on what would be most relevant to remember 
        for future interactions."""
        
        # Build the conversation text
        conversation_text = f"Conversation between User and {conversation.character.name}:\n\n"
        
        for msg in messages:
            sender = "User" if msg.sender == "user" else conversation.character.name
            conversation_text += f"{sender}: {msg.content}\n\n"
        
        user_prompt = f"""Please summarize the following conversation:
        
        {conversation_text}
        
        Create a concise but informative summary that highlights key points, emotions, 
        and any important information revealed during this conversation segment.
        """
        
        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.5,
            max_tokens=500
        )
        
        # Log token usage - Fixed to use object properties
        token_usage = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens
        }
        
        self._log_token_usage(
            feature='memory_summarization',
            tokens_used=token_usage['total_tokens'],
            character_id=conversation.character.id,
            conversation_id=conversation.id
        )
        
        return {
            'summary': response.choices[0].message.content,
            'token_usage': token_usage,
        }
    
    def _log_token_usage(self, feature, tokens_used, character_id=None, conversation_id=None, 
                     story_id=None, world_id=None):
        """Log token usage to the database"""
        # Create token usage record
        TokenUsage.objects.create(
            user=self.user,
            feature=feature,
            tokens_used=tokens_used,
            character_id=character_id,
            conversation_id=conversation_id,
            story_id=story_id,
            world_id=world_id
        )
        
        # Get the user's token limit object and update it
        token_limit_obj = UserTokenLimit.objects.get(user=self.user)
        token_limit_obj.update_token_usage(amount=tokens_used, feature=feature)
        
        return tokens_used