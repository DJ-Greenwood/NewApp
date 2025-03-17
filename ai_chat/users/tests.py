from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from token_management.models import UserTokenLimit, TokenUsage

User = get_user_model()

class CustomUserModelTests(TestCase):
    """Test cases for the CustomUser model"""
    
    def setUp(self):
        """Set up test data"""
        # Create a basic test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Create token limit for the user
        self.token_limit = UserTokenLimit.objects.create(
            user=self.user,
            monthly_limit=50000
        )
    
    def test_user_creation(self):
        """Test that a user can be created and saved"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertTrue(self.user.check_password('testpassword123'))
        self.assertEqual(self.user.subscription_tier, 'free')
        self.assertEqual(self.user.token_usage_this_month, 0)
        self.assertTrue(self.user.is_active)
        self.assertFalse(self.user.is_staff)
    
    def test_user_str_method(self):
        """Test the string representation of a user"""
        self.assertEqual(str(self.user), 'testuser')
    
    def test_token_usage_update(self):
        """Test updating token usage"""
        initial_usage = self.user.token_usage_this_month
        self.user.update_token_usage(500, feature='character_chat')
        
        # Refresh from database
        self.user.refresh_from_db()
        
        # Check usage was updated
        self.assertEqual(self.user.token_usage_this_month, initial_usage + 500)
        
        # Check TokenUsage record was created
        token_usage = TokenUsage.objects.filter(user=self.user).first()
        self.assertIsNotNone(token_usage)
        self.assertEqual(token_usage.tokens_used, 500)
        self.assertEqual(token_usage.feature, 'character_chat')
    
    def test_token_percentage_calculation(self):
        """Test token percentage calculation"""
        # Set up some token usage
        self.user.token_usage_this_month = 25000
        self.user.save()
        
        # Calculate percentage (should be 50% of 50000)
        percentage = self.user.get_token_percent_used()
        self.assertEqual(percentage, 50.0)
        
        # Test with zero limit (should return 100%)
        self.token_limit.monthly_limit = 0
        self.token_limit.save()
        percentage = self.user.get_token_percent_used()
        self.assertEqual(percentage, 100)
        
        # Reset limit and test with usage above limit (should cap at 100%)
        self.token_limit.monthly_limit = 10000
        self.token_limit.save()
        percentage = self.user.get_token_percent_used()
        self.assertEqual(percentage, 100)
    
    def test_monthly_token_reset(self):
        """Test resetting monthly token usage"""
        # Set up some token usage
        self.user.token_usage_this_month = 30000
        self.user.token_reset_date = timezone.now().date() - timedelta(days=32)
        self.user.save()
        
        # Reset tokens
        self.user.reset_monthly_tokens()
        
        # Check usage was reset
        self.assertEqual(self.user.token_usage_this_month, 0)
        self.assertEqual(self.user.token_reset_date, timezone.now().date())
    
    def test_preferences_default(self):
        """Test that preferences default to an empty dict"""
        self.assertEqual(self.user.preferences, {})
    
    def test_preferences_update(self):
        """Test updating user preferences"""
        # Set preferences
        self.user.preferences = {
            'theme': 'dark',
            'enable_animations': True,
            'default_ai_model': 'gpt-4'
        }
        self.user.save()
        
        # Refresh from database
        self.user.refresh_from_db()
        
        # Check preferences were saved
        self.assertEqual(self.user.preferences['theme'], 'dark')
        self.assertTrue(self.user.preferences['enable_animations'])
        self.assertEqual(self.user.preferences['default_ai_model'], 'gpt-4')
    
    def test_profile_fields(self):
        """Test setting and retrieving profile fields"""
        self.user.bio = "This is a test biography"
        self.user.location = "Test City"
        self.user.website = "https://example.com"
        self.user.save()
        
        # Refresh from database
        self.user.refresh_from_db()
        
        # Check fields were saved
        self.assertEqual(self.user.bio, "This is a test biography")
        self.assertEqual(self.user.location, "Test City")
        self.assertEqual(self.user.website, "https://example.com")
    
    def test_subscription_upgrade(self):
        """Test upgrading a user's subscription"""
        # Check initial tier
        self.assertEqual(self.user.subscription_tier, 'free')
        
        # Upgrade to basic
        self.user.subscription_tier = 'basic'
        self.user.subscription_start_date = timezone.now()
        self.user.subscription_end_date = timezone.now() + timedelta(days=30)
        self.user.save()
        
        # Refresh from database
        self.user.refresh_from_db()
        
        # Check tier was upgraded
        self.assertEqual(self.user.subscription_tier, 'basic')
        self.assertIsNotNone(self.user.subscription_start_date)
        self.assertIsNotNone(self.user.subscription_end_date)


class UserViewTests(TestCase):
    """Test cases for user-related views"""
    
    def setUp(self):
        """Set up test data"""
        self.signup_url = reverse('users:register')
        self.login_url = reverse('users:login')
        self.profile_url = reverse('users:profile')
        
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        # Create token limit for the user
        self.token_limit = UserTokenLimit.objects.create(
            user=self.user,
            monthly_limit=50000
        )
        
        # User credentials for login tests
        self.credentials = {
            'username': 'testuser',
            'password': 'testpassword123'
        }
    
    def test_signup_page_load(self):
        """Test that signup page loads correctly"""
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/signup.html')
    
    def test_signup_form_submission(self):
        """Test user registration through the signup form"""
        response = self.client.post(self.signup_url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'newuserpassword123',
            'password2': 'newuserpassword123'
        })
        
        # Should redirect on successful signup
        self.assertEqual(response.status_code, 302)
        
        # Check user was created
        self.assertTrue(User.objects.filter(username='newuser').exists())
        
        # Check token limit was created
        new_user = User.objects.get(username='newuser')
        self.assertTrue(UserTokenLimit.objects.filter(user=new_user).exists())
        
        # Check default preferences were set
        self.assertIn('theme', new_user.preferences)
    
    def test_login(self):
        """Test user login"""
        response = self.client.post(self.login_url, self.credentials)
        
        # Should redirect on successful login
        self.assertEqual(response.status_code, 302)
        
        # Check user is logged in
        self.assertTrue(response.wsgi_request.user.is_authenticated)
    
    def test_profile_access_authentication(self):
        """Test that profile page requires authentication"""
        # Try accessing without login
        response = self.client.get(self.profile_url)
        
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
        
        # Login and try again
        self.client.login(**self.credentials)
        response = self.client.get(self.profile_url)
        
        # Should be accessible now
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'users/profile.html')